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
        self.validate_dates()
        self.set_property_from_unit()
        self.calculate_commission()
        self.calculate_item_amounts()
        self.build_invoice_schedule()

    def on_update(self):
        if self.status == "Active" and self.unit:
            self.update_unit_status("Rented" if self.contract_type == "Rent" else "Sold")

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

    def set_property_from_unit(self):
        if not self.unit:
            return

        unit_property = frappe.db.get_value("Unit Master", self.unit, "property")
        if unit_property and not self.property:
            self.property = unit_property

        if unit_property and self.property and self.property != unit_property:
            frappe.throw(_("Selected Unit does not belong to the selected Property"))

    def calculate_commission(self):
        if self.contract_type == "Sale":
            self.commission_amount = flt(self.sale_amount) * flt(self.commission_percentage) / 100.0
        else:
            self.commission_amount = 0

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

        self._build_rent_schedule(existing_by_due)

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

    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": lease.company,
            "customer": lease.customer,
            "posting_date": today(),
            "due_date": row.due_date or today(),
            "items": items,
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
