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
def make_journal_entry(maintenance_request):
    """Create a Journal Entry for maintenance expense from the services/items total."""
    doc = frappe.get_doc("Maintenance Request", maintenance_request)
    doc.check_permission("write")

    if doc.docstatus != 1:
        frappe.throw(_("Submit the Maintenance Request before creating a Journal Entry"))

    if doc.journal_entry:
        frappe.throw(_("Journal Entry {0} is already linked").format(doc.journal_entry))

    if not flt(doc.total_cost):
        frappe.throw(_("Total cost must be greater than zero"))

    settings = frappe.get_single("Property Management Settings")
    expense_account = settings.maintenance_expense_account
    if not expense_account:
        frappe.throw(_("Set Maintenance Expense Account in Property Management Settings"))

    company = doc.company or _resolve_company(doc)
    company_doc = frappe.get_doc("Company", company)
    credit_account = settings.maintenance_credit_account or company_doc.default_cash_account
    if credit_account and _account_requires_party(credit_account):
        credit_account = company_doc.default_cash_account or company_doc.default_bank_account
    if not credit_account or _account_requires_party(credit_account):
        frappe.throw(_("Set Maintenance Credit Account in Property Management Settings to a Cash/Bank account"))

    cost_center = None
    if doc.property:
        cost_center = frappe.db.get_value("Property", doc.property, "cost_center")

    accounts = [
        {
            "account": expense_account,
            "debit_in_account_currency": flt(doc.total_cost),
            "cost_center": cost_center,
        },
        {
            "account": credit_account,
            "credit_in_account_currency": flt(doc.total_cost),
            "cost_center": cost_center,
        },
    ]

    je = frappe.get_doc(
        {
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": company,
            "posting_date": today(),
            "user_remark": _("Maintenance Request: {0} - {1}").format(doc.name, doc.subject or ""),
            "accounts": accounts,
        }
    )
    je.insert(ignore_permissions=False)
    je.submit()

    doc.db_set("journal_entry", je.name)
    return je.name


def _resolve_company(doc):
    if doc.property:
        company = frappe.db.get_value("Property", doc.property, "company")
        if company:
            return company
    return (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )


def _account_requires_party(account):
    if not account:
        return False
    account_type = frappe.db.get_value("Account", account, "account_type")
    return account_type in ("Receivable", "Payable")
