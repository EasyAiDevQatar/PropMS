# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import date_diff, getdate, today


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Lease Agreement"), "fieldname": "lease_agreement", "fieldtype": "Link", "options": "Lease Agreement", "width": 160},
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Property", "width": 140},
        {"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Unit Master", "width": 120},
        {"label": _("Tenant"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 100},
        {"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Date", "width": 100},
        {"label": _("Days Until Expiry"), "fieldname": "days_until_expiry", "fieldtype": "Int", "width": 140},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Monthly Rent"), "fieldname": "monthly_rent", "fieldtype": "Currency", "width": 120},
    ]


def get_data(filters):
    where = ["la.end_date IS NOT NULL"]
    args = {}

    if filters.get("from_date"):
        where.append("la.end_date >= %(from_date)s")
        args["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        where.append("la.end_date <= %(to_date)s")
        args["to_date"] = filters.get("to_date")

    if filters.get("property"):
        where.append("la.property = %(property)s")
        args["property"] = filters.get("property")

    if filters.get("unit"):
        where.append("la.unit = %(unit)s")
        args["unit"] = filters.get("unit")

    if filters.get("tenant"):
        where.append("la.customer = %(tenant)s")
        args["tenant"] = filters.get("tenant")

    where.append("la.status NOT IN ('Cancelled', 'Finished')")

    rows = frappe.db.sql(
        """
        SELECT la.name AS lease_agreement,
               la.property,
               la.unit,
               la.customer,
               la.start_date,
               la.end_date,
               la.status,
               la.monthly_rent
        FROM `tabLease Agreement` la
        WHERE {where}
        ORDER BY la.end_date ASC
        """.format(where=" AND ".join(where)),
        args,
        as_dict=True,
    )

    today_date = getdate(today())
    for row in rows:
        if row.end_date:
            row.days_until_expiry = date_diff(getdate(row.end_date), today_date)
        else:
            row.days_until_expiry = None

    return rows
