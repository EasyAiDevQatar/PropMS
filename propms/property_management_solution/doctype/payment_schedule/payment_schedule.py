# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class PaymentSchedule(Document):
    def validate(self):
        self.set_contract_values()
        self.set_amount_from_charge()
        self.validate_invoice_status()

    def set_contract_values(self):
        if not self.contract:
            return

        contract = frappe.db.get_value(
            "Lease Agreement",
            self.contract,
            ["customer", "unit"],
            as_dict=True,
        )
        if not contract:
            return

        if contract.customer and not self.customer:
            self.customer = contract.customer
        if contract.unit and not self.unit:
            self.unit = contract.unit

    def set_amount_from_charge(self):
        if self.amount or not self.charge:
            return

        self.amount = frappe.db.get_value("Charges Setup", self.charge, "default_amount")

    def validate_invoice_status(self):
        if self.sales_invoice and self.status == "Pending":
            self.status = "Invoiced"


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_units_for_contract(doctype, txt, searchfield, start, page_len, filters):
    filters = filters or {}
    property_name = frappe.db.get_value("Lease Agreement", filters.get("contract"), "property")
    if not property_name:
        return []

    return frappe.db.sql(
        """
        select name, unit_number
        from `tabUnit Master`
        where property = %(property)s
            and ({searchfield} like %(txt)s or unit_number like %(txt)s)
        order by name
        limit %(start)s, %(page_len)s
        """.format(searchfield=searchfield),
        {
            "property": property_name,
            "txt": "%%%s%%" % txt,
            "start": start,
            "page_len": page_len,
        },
    )


@frappe.whitelist()
def make_sales_invoice(payment_schedule, posting_date=None):
    schedule = frappe.get_doc("Payment Schedule", payment_schedule)
    schedule.check_permission("write")

    invoice = create_sales_invoice_from_payment_schedule(schedule, posting_date)

    schedule.db_set("sales_invoice", invoice.name)
    schedule.db_set("status", "Invoiced")
    if schedule.contract:
        frappe.db.set_value(
            "Lease Agreement",
            schedule.contract,
            "linked_sales_invoice",
            invoice.name,
        )

    return invoice.name


def create_sales_invoice_from_payment_schedule(schedule, posting_date=None):
    if schedule.sales_invoice:
        frappe.throw(_("Sales Invoice {0} is already linked to this schedule").format(schedule.sales_invoice))
    if schedule.status == "Paid":
        frappe.throw(_("Paid payment schedules cannot be invoiced again"))
    if not schedule.customer:
        frappe.throw(_("Customer is required to generate Sales Invoice"))
    if flt(schedule.amount) <= 0:
        frappe.throw(_("Amount must be greater than zero"))

    company = get_company(schedule)
    charge = get_charge(schedule)
    unit = get_unit(schedule)
    taxes_and_charges = charge.get("tax_template") or frappe.db.get_value(
        "Company", company, "default_tax_template"
    )

    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": company,
            "posting_date": posting_date or today(),
            "customer": schedule.customer,
            "due_date": schedule.due_date,
            "taxes_and_charges": taxes_and_charges,
            "items": [get_invoice_item(schedule, charge, unit)],
        }
    )

    if taxes_and_charges:
        add_taxes(invoice, taxes_and_charges)

    invoice.calculate_taxes_and_totals()
    invoice.insert()
    return invoice


def get_company(schedule):
    property_name = None
    if schedule.contract:
        property_name = frappe.db.get_value("Lease Agreement", schedule.contract, "property")
    if not property_name and schedule.unit:
        property_name = frappe.db.get_value("Unit Master", schedule.unit, "property")

    company = None
    if property_name:
        company = frappe.db.get_value("Property", property_name, "company")

    company = (
        company
        or frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )
    if not company:
        frappe.throw(_("Company is required to generate Sales Invoice"))

    return company


def get_charge(schedule):
    charge_name = schedule.charge or get_charge_from_description(schedule) or get_charge_from_contract(schedule)
    if not charge_name:
        frappe.throw(_("Select a Charge on the Payment Schedule before generating an invoice"))

    charge = frappe.db.get_value(
        "Charges Setup",
        charge_name,
        ["erp_item", "income_account", "tax_template"],
        as_dict=True,
    )
    if not charge or not charge.erp_item:
        frappe.throw(_("Charge {0} must have an ERP Item").format(charge_name))

    return charge


def get_charge_from_description(schedule):
    if not schedule.description:
        return None

    if frappe.db.exists("Charges Setup", schedule.description):
        return schedule.description

    return None


def get_charge_from_contract(schedule):
    if not schedule.contract:
        return None

    contract_type = frappe.db.get_value("Lease Agreement", schedule.contract, "contract_type")
    if not contract_type:
        return None

    return frappe.db.get_value("Charges Setup", {"charge_type": contract_type}, "name")


def get_unit(schedule):
    if not schedule.unit:
        return {}

    return frappe.db.get_value(
        "Unit Master",
        schedule.unit,
        ["income_account", "cost_center"],
        as_dict=True,
    ) or {}


def get_invoice_item(schedule, charge, unit):
    item = {
        "item_code": charge.erp_item,
        "description": schedule.description,
        "qty": 1,
        "rate": schedule.amount,
    }

    income_account = charge.get("income_account") or unit.get("income_account")
    if income_account:
        item["income_account"] = income_account

    if unit.get("cost_center"):
        item["cost_center"] = unit.cost_center

    return item


def add_taxes(invoice, taxes_and_charges):
    taxes = get_taxes_and_charges("Sales Taxes and Charges Template", taxes_and_charges)
    for tax in taxes:
        invoice.append("taxes", tax)
