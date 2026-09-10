# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    add_months,
    flt,
    getdate,
    today,
)


FREQUENCY_MONTHS = {
    "Monthly": 1,
    "Quarterly": 3,
    "Half Yearly": 6,
    "Yearly": 12,
}


class LeaseAgreement(Document):
    def validate(self):
        self.set_contract_number()
        self.set_contract_display_name()
        self.validate_dates()
        self.set_property_from_unit()
        self.calculate_commission()
        self.calculate_rent_commission()
        self.calculate_item_amounts()
        self.build_invoice_schedule()
        self.set_linked_payment_count()

    def on_submit(self):
        self.db_set("status", "Active")
        if self.unit:
            if self.contract_type == "Sale":
                self.update_unit_status("Sold")
                if self.property:
                    frappe.db.set_value("Property", self.property, "status", "Sold")
            else:
                self.update_unit_status("Rented")

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        if self.unit:
            self.update_unit_status("Available")

    def on_update(self):
        if self.docstatus == 1 and self.status == "Active" and self.unit:
            unit_status = "Sold" if self.contract_type == "Sale" else "Rented"
            self.update_unit_status(unit_status)

    def on_change(self):
        if self.status in ("Cancelled", "Finished", "Expired") and self.unit:
            self.update_unit_status("Available")

    def update_unit_status(self, status):
        try:
            current = frappe.db.get_value("Unit Master", self.unit, "status")
            if current != status:
                frappe.db.set_value("Unit Master", self.unit, "status", status)
        except Exception:
            frappe.log_error(
                "Failed to update Unit Master status",
                "Lease Agreement {0}".format(self.name or ""),
            )

    def validate_dates(self):
        if self.end_date and self.start_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("End Date cannot be before Start Date"))

    def set_contract_number(self):
        if self.contract_number:
            return

        if self.amended_from:
            self.contract_number = (
                frappe.db.get_value("Lease Agreement", self.amended_from, "contract_number")
                or self.name
            )
        else:
            self.contract_number = self.name

    def set_contract_display_name(self):
        parts = []
        if self.customer_name:
            parts.append(self.customer_name)
        elif self.customer:
            parts.append(self.customer)
        if self.property:
            property_name = frappe.db.get_value("Property", self.property, "property_name")
            parts.append(property_name or self.property)
        self.contract_display_name = " - ".join(parts) or self.contract_number or self.name

    def set_property_from_unit(self):
        if not self.unit:
            return

        unit_property = frappe.db.get_value("Unit Master", self.unit, "property")
        if unit_property and not self.property:
            self.property = unit_property

        if unit_property and self.property and self.property != unit_property:
            frappe.throw(_("Selected Unit does not belong to the selected Property"))

    def set_linked_payment_count(self):
        self.linked_payment_count = get_linked_payment_count(self.name) if self.name else 0

    def calculate_commission(self):
        if self.contract_type == "Sale":
            self.commission_amount = flt(self.sale_amount) * flt(self.commission_percentage) / 100.0
        else:
            self.commission_amount = 0

    def calculate_rent_commission(self):
        if self.contract_type == "Rent" and self.rent_commission_only:
            self.rent_commission_amount = flt(self.monthly_rent) * flt(self.rent_commission_months or 1)
        else:
            self.rent_commission_amount = 0

    def calculate_item_amounts(self):
        for row in self.items or []:
            row.amount = flt(row.qty or 1) * flt(row.rate or 0)

    def build_invoice_schedule(self):
        """Regenerate schedule rows. Never auto-creates Sales Invoices."""
        if not self.start_date:
            return

        existing_by_due = {}
        for row in list(self.invoice_schedule or []):
            if row.sales_invoice:
                existing_by_due[str(row.due_date)] = row
        invoiced_rows = list(existing_by_due.values())

        self.invoice_schedule = []
        for row in invoiced_rows:
            self.append("invoice_schedule", row)

        if self.contract_type == "Sale":
            self._build_sale_schedule(existing_by_due)
            return

        if self.contract_type == "Rent" and self.rent_commission_only:
            self._build_rent_commission_schedule(existing_by_due)
            return

        self._build_rent_schedule(existing_by_due)

    def _build_rent_commission_schedule(self, existing_by_due):
        """Single commission invoice for brokerage rent contracts."""
        due_date = self.start_date
        if str(due_date) in existing_by_due:
            return

        amount = flt(self.rent_commission_amount)
        if amount <= 0:
            return

        self.append(
            "invoice_schedule",
            {
                "due_date": due_date,
                "period_start_date": self.start_date,
                "period_end_date": self.end_date or self.start_date,
                "amount": amount,
                "deposit_amount": 0,
                "total_amount": amount,
                "status": "Pending",
            },
        )

    def _build_sale_schedule(self, existing_by_due):
        """For sale contracts a single commission invoice is generated."""
        due_date = self.start_date
        if str(due_date) in existing_by_due:
            return

        self.append(
            "invoice_schedule",
            {
                "due_date": due_date,
                "period_start_date": self.start_date,
                "period_end_date": self.end_date or self.start_date,
                "amount": flt(self.commission_amount),
                "deposit_amount": 0,
                "total_amount": flt(self.commission_amount),
                "status": "Pending",
            },
        )

    def _build_rent_schedule(self, existing_by_due):
        months = FREQUENCY_MONTHS.get(self.payment_frequency or "Monthly", 1)
        rent_per_period = self._get_rent_per_period(months)
        if rent_per_period <= 0 and not (self.items or []):
            return

        first_invoice_extras, recurring_amount = self._split_items(months)
        if rent_per_period:
            recurring_amount += rent_per_period

        deposit_amount = (
            flt(self.security_deposit) if self.include_deposit_in_first_invoice else 0
        )

        end_date = getdate(self.end_date) if self.end_date else add_months(
            getdate(self.start_date), 12
        )
        period_start = getdate(self.start_date)
        first = True

        guard = 0
        while period_start <= end_date and guard < 600:
            period_end = add_days(add_months(period_start, months), -1)
            if period_end > end_date:
                period_end = end_date

            row_amount = recurring_amount
            row_deposit = 0
            if first:
                row_amount += first_invoice_extras
                row_deposit = deposit_amount

            due = period_start
            if str(due) not in existing_by_due:
                self.append(
                    "invoice_schedule",
                    {
                        "due_date": due,
                        "period_start_date": period_start,
                        "period_end_date": period_end,
                        "amount": row_amount,
                        "deposit_amount": row_deposit,
                        "total_amount": flt(row_amount) + flt(row_deposit),
                        "status": "Pending",
                    },
                )

            first = False
            period_start = add_days(period_end, 1)
            guard += 1

    def _get_rent_per_period(self, months):
        if not self.monthly_rent:
            return 0
        return flt(self.monthly_rent) * months

    def _split_items(self, months):
        first_invoice_extras = 0
        recurring_amount = 0
        for row in self.items or []:
            if row.is_deposit:
                continue
            amount = flt(row.amount or (flt(row.qty or 1) * flt(row.rate or 0)))
            frequency = row.frequency or "Monthly"
            if row.include_in_first_invoice or frequency == "One Time":
                first_invoice_extras += amount
                continue
            row_months = FREQUENCY_MONTHS.get(frequency, 1)
            if row_months == 0:
                continue
            recurring_amount += amount * months / row_months
        return first_invoice_extras, recurring_amount


def get_linked_payment_count(lease_agreement):
    deposit_received, deposit_return = frappe.db.get_value(
        "Lease Agreement",
        lease_agreement,
        ["security_deposit_payment_entry", "security_deposit_return_payment_entry"],
    ) or ("", "")

    rows = frappe.db.sql(
        """
        SELECT DISTINCT pe.name
        FROM `tabPayment Entry` pe
        LEFT JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        LEFT JOIN `tabSales Invoice` si
            ON per.reference_doctype = 'Sales Invoice'
           AND per.reference_name = si.name
        WHERE pe.docstatus = 1
          AND (
            pe.propms_lease_agreement = %(lease)s
            OR si.propms_lease_agreement = %(lease)s
            OR pe.name = %(deposit_received)s
            OR pe.name = %(deposit_return)s
          )
        """,
        {
            "lease": lease_agreement,
            "deposit_received": deposit_received or "",
            "deposit_return": deposit_return or "",
        },
    )
    return len(rows)


@frappe.whitelist()
def sync_invoice_schedule_payments(lease_agreement):
    """Backfill payment entry links and paid status on invoice schedule rows."""
    doc = frappe.get_doc("Lease Agreement", lease_agreement)
    doc.check_permission("read")

    changed = False
    for row in doc.invoice_schedule or []:
        if not row.sales_invoice:
            continue

        si = frappe.db.get_value(
            "Sales Invoice",
            row.sales_invoice,
            ["status", "outstanding_amount"],
            as_dict=True,
        )
        if not si:
            continue

        payment_entry = _get_latest_payment_entry_for_schedule_row(doc.name, row.sales_invoice)
        if payment_entry and row.payment_entry != payment_entry:
            row.payment_entry = payment_entry
            changed = True

        if flt(si.outstanding_amount) <= 0 and si.status == "Paid" and row.status != "Paid":
            row.status = "Paid"
            changed = True

    if changed:
        doc.save(ignore_permissions=True)

    count = get_linked_payment_count(doc.name)
    if doc.linked_payment_count != count:
        doc.db_set("linked_payment_count", count)

    return {"linked_payment_count": count, "updated": changed}


def _get_latest_payment_entry_for_schedule_row(lease, sales_invoice):
    result = frappe.db.sql(
        """
        SELECT pe.name
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        WHERE pe.docstatus = 1
          AND per.reference_doctype = 'Sales Invoice'
          AND per.reference_name = %(sales_invoice)s
          AND (
            pe.propms_lease_agreement = %(lease)s
            OR pe.propms_lease_agreement IS NULL
            OR pe.propms_lease_agreement = ''
          )
        ORDER BY pe.posting_date DESC, pe.creation DESC
        LIMIT 1
        """,
        {"sales_invoice": sales_invoice, "lease": lease},
    )
    return result[0][0] if result else None


@frappe.whitelist()
def fetch_unit_services(unit):
    """Return Unit Master services as Lease Agreement Item rows."""
    if not unit:
        return []

    services = frappe.get_all(
        "Unit Service",
        filters={"parent": unit, "parenttype": "Unit Master"},
        fields=["item", "item_name", "description", "frequency", "rate", "tax_template"],
        order_by="idx",
    )

    result = []
    for service in services:
        result.append(
            {
                "item": service.item,
                "item_name": service.item_name,
                "description": service.description,
                "frequency": service.frequency or "Monthly",
                "qty": 1,
                "rate": service.rate,
                "amount": service.rate,
                "tax_template": service.tax_template,
            }
        )
    return result


@frappe.whitelist()
def make_sales_invoice_for_schedule(lease_agreement, schedule_row_name):
    """Create a Sales Invoice for one schedule row."""
    doc = frappe.get_doc("Lease Agreement", lease_agreement)
    doc.check_permission("write")

    row = None
    for r in doc.invoice_schedule:
        if r.name == schedule_row_name:
            row = r
            break

    if not row:
        frappe.throw(_("Schedule row not found"))
    if row.sales_invoice:
        frappe.throw(_("Sales Invoice {0} already linked").format(row.sales_invoice))

    invoice = _build_sales_invoice(doc, row)
    invoice.insert()

    row.sales_invoice = invoice.name
    row.status = "Invoiced"
    doc.save(ignore_permissions=True)
    return invoice.name


def _build_sales_invoice(lease, row):
    items = []

    if lease.contract_type == "Sale":
        commission_item = _get_commission_item(lease.company)
        items.append(
            {
                "item_code": commission_item,
                "qty": 1,
                "rate": flt(lease.commission_amount),
                "description": _("Sale commission ({0}%) on {1}").format(
                    flt(lease.commission_percentage), lease.unit or lease.property
                ),
            }
        )
    elif lease.contract_type == "Rent" and lease.rent_commission_only:
        commission_item = _get_commission_item(lease.company)
        items.append(
            {
                "item_code": commission_item,
                "qty": 1,
                "rate": flt(lease.rent_commission_amount),
                "description": _("Rent commission ({0} month(s)) on {1}").format(
                    flt(lease.rent_commission_months or 1), lease.unit or lease.property
                ),
            }
        )
    else:
        if lease.monthly_rent:
            months = FREQUENCY_MONTHS.get(lease.payment_frequency or "Monthly", 1)
            rent_item = _get_rent_item(lease.company)
            items.append(
                {
                    "item_code": rent_item,
                    "qty": months,
                    "rate": flt(lease.monthly_rent),
                    "description": _("Rent for {0} - {1}").format(
                        row.period_start_date, row.period_end_date
                    ),
                }
            )

        is_first = (
            lease.invoice_schedule
            and lease.invoice_schedule[0].name == row.name
        )

        for item_row in lease.items or []:
            if item_row.is_deposit:
                continue
            if not is_first and (item_row.include_in_first_invoice or item_row.frequency == "One Time"):
                continue
            items.append(
                {
                    "item_code": item_row.item,
                    "qty": item_row.qty or 1,
                    "rate": flt(item_row.rate),
                    "description": item_row.description or item_row.item_name,
                }
            )

        if is_first and flt(row.deposit_amount):
            deposit_item = _get_deposit_item(lease.company)
            items.append(
                {
                    "item_code": deposit_item,
                    "qty": 1,
                    "rate": flt(row.deposit_amount),
                    "description": _("Security deposit"),
                }
            )

    if not items:
        frappe.throw(_("No items to invoice"))

    customer = lease.customer
    if lease.contract_type == "Sale" and lease.buyer:
        customer = lease.buyer

    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": lease.company,
            "customer": customer,
            "posting_date": today(),
            "due_date": row.due_date or today(),
            "items": items,
            "propms_lease_agreement": lease.name,
            "propms_property": lease.property,
            "propms_unit": lease.unit,
        }
    )
    return invoice


def _get_commission_item(company):
    return _get_or_create_default_item("Sale Commission", company)


def _get_rent_item(company):
    return _get_or_create_default_item("Rent Income", company)


def _get_deposit_item(company):
    return _get_or_create_default_item("Security Deposit", company)


def _get_or_create_default_item(item_name, company):
    if frappe.db.exists("Item", item_name):
        return item_name
    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_name,
            "item_name": item_name,
            "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 0,
        }
    )
    item.insert(ignore_permissions=True)
    return item.name


@frappe.whitelist()
def make_deposit_return_payment_entry(lease_agreement):
    """Create a Payment Entry to return the security deposit to the tenant."""
    lease = frappe.get_doc("Lease Agreement", lease_agreement)
    lease.check_permission("write")

    if not flt(lease.security_deposit):
        frappe.throw(_("No security deposit amount on this contract"))

    if lease.security_deposit_return_payment_entry:
        frappe.throw(
            _("Deposit return payment already created: {0}").format(
                lease.security_deposit_return_payment_entry
            )
        )

    if lease.security_deposit_status not in ("Received",):
        frappe.throw(_("Security deposit must be marked as Received before returning"))

    settings = frappe.get_single("Property Management Settings")
    company = lease.company or settings.company
    if not company:
        frappe.throw(_("Company is required on the lease agreement"))

    company_doc = frappe.get_doc("Company", company)
    pe = frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "party_type": "Customer",
            "party": lease.customer,
            "company": company,
            "posting_date": today(),
            "paid_from": company_doc.default_cash_account,
            "paid_to": company_doc.default_receivable_account,
            "paid_amount": flt(lease.security_deposit),
            "received_amount": flt(lease.security_deposit),
            "reference_no": lease.name,
            "reference_date": today(),
            "remarks": _("Security deposit return for {0}").format(lease.name),
            "mode_of_payment": settings.security_deposit_payment_type,
        }
    )
    pe.propms_lease_agreement = lease.name
    pe.propms_property = lease.property
    pe.propms_unit = lease.unit
    pe.insert(ignore_permissions=False)
    pe.submit()

    lease.db_set(
        {
            "security_deposit_return_payment_entry": pe.name,
            "security_deposit_status": "Returned",
        }
    )
    lease.set_linked_payment_count()
    lease.db_set("linked_payment_count", lease.linked_payment_count)
    return pe.name