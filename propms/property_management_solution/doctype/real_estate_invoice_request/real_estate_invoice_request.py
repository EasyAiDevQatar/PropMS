# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document

from propms.property_management_solution.doctype.payment_schedule.payment_schedule import (
    make_sales_invoice,
)


class RealEstateInvoiceRequest(Document):
    def validate(self):
        self.set_schedule_values()

    def set_schedule_values(self):
        if not self.payment_schedule:
            return

        schedule = frappe.db.get_value(
            "Payment Schedule",
            self.payment_schedule,
            ["customer", "unit", "due_date", "amount", "sales_invoice"],
            as_dict=True,
        )
        if not schedule:
            return

        self.customer = schedule.customer
        self.unit = schedule.unit
        self.due_date = schedule.due_date
        self.amount = schedule.amount
        if schedule.sales_invoice:
            self.sales_invoice = schedule.sales_invoice
            self.status = "Invoiced"


@frappe.whitelist()
def generate_sales_invoice(invoice_request):
    request = frappe.get_doc("Real Estate Invoice Request", invoice_request)
    request.check_permission("write")

    if request.status == "Cancelled":
        frappe.throw(_("Cancelled requests cannot generate invoices"))
    if request.sales_invoice:
        return request.sales_invoice

    sales_invoice = make_sales_invoice(request.payment_schedule, request.posting_date)
    request.db_set("sales_invoice", sales_invoice)
    request.db_set("status", "Invoiced")

    return sales_invoice
