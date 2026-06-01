# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class MaintenanceRequest(Document):
    def autoname(self):
        # Frappe will use naming_series (MR-.YYYY.-) automatically; the
        # explicit hook here just guards against an empty series.
        if not self.naming_series:
            self.naming_series = "MR-.YYYY.-"

    def validate(self):
        self.set_property_from_unit()
        self.calculate_totals()
        self.set_unit_under_maintenance()

    def calculate_totals(self):
        total = 0
        for row in self.items or []:
            row.amount = flt(row.qty or 1) * flt(row.rate or 0)
            total += flt(row.amount)
        self.total_cost = total

    def set_property_from_unit(self):
        if not self.unit:
            return
        unit_property = frappe.db.get_value("Unit Master", self.unit, "property")
        if unit_property and not self.property:
            self.property = unit_property

    def set_unit_under_maintenance(self):
        if (
            self.unit
            and self.status in ("Open", "In Progress")
            and frappe.db.get_value("Unit Master", self.unit, "status") == "Available"
        ):
            frappe.db.set_value("Unit Master", self.unit, "status", "Under Maintenance")

    def on_update(self):
        if self.status in ("Resolved", "Closed", "Cancelled") and self.unit:
            current = frappe.db.get_value("Unit Master", self.unit, "status")
            if current == "Under Maintenance":
                frappe.db.set_value("Unit Master", self.unit, "status", "Available")


@frappe.whitelist()
def make_purchase_invoice(maintenance_request):
    """Create a Purchase Invoice from items used in maintenance.

    Items are grouped by supplier - one Purchase Invoice per supplier. If no
    supplier is set on a row, a default placeholder Supplier 'Maintenance
    Supplier' is used (created on the fly if needed).
    """
    doc = frappe.get_doc("Maintenance Request", maintenance_request)
    doc.check_permission("write")

    if doc.purchase_invoice:
        frappe.throw(_("Purchase Invoice {0} is already linked").format(doc.purchase_invoice))

    if not (doc.items or []):
        frappe.throw(_("Add at least one item before creating a Purchase Invoice"))

    grouped = {}
    for row in doc.items:
        supplier = row.supplier or _ensure_default_supplier()
        grouped.setdefault(supplier, []).append(row)

    invoices = []
    for supplier, rows in grouped.items():
        invoice = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "supplier": supplier,
                "company": doc.company or _resolve_company(doc),
                "posting_date": today(),
                "due_date": today(),
                "items": [
                    {
                        "item_code": r.item,
                        "qty": r.qty or 1,
                        "rate": flt(r.rate),
                        "description": r.description or r.item_name,
                        "uom": r.uom,
                    }
                    for r in rows
                ],
                "remarks": _("Maintenance Request: {0} - {1}").format(doc.name, doc.subject or ""),
                "propms_maintenance_request": doc.name,
                "propms_property": doc.property,
                "propms_unit": doc.unit,
            }
        )
        invoice.insert(ignore_permissions=False)
        invoices.append(invoice.name)

    doc.db_set("purchase_invoice", invoices[0])
    return invoices


def _resolve_company(doc):
    if doc.property:
        company = frappe.db.get_value("Property", doc.property, "company")
        if company:
            return company
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def _ensure_default_supplier():
    name = "Maintenance Supplier"
    if frappe.db.exists("Supplier", name):
        return name
    supplier_group = (
        frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
        or "All Supplier Groups"
    )
    frappe.get_doc(
        {
            "doctype": "Supplier",
            "supplier_name": name,
            "supplier_group": supplier_group,
        }
    ).insert(ignore_permissions=True)
    return name
