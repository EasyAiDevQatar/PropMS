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
        {"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Property Unit", "width": 130},
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Property", "width": 140},
        {"label": _("Property Type"), "fieldname": "property_type", "fieldtype": "Link", "options": "Property Type", "width": 120},
        {"label": _("Unit Status"), "fieldname": "unit_status", "fieldtype": "Data", "width": 110},
        {"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Lease Agreement"), "fieldname": "lease_agreement", "fieldtype": "Link", "options": "Lease Agreement", "width": 150},
        {"label": _("Contract Type"), "fieldname": "contract_type", "fieldtype": "Data", "width": 100},
        {"label": _("Lease End Date"), "fieldname": "end_date", "fieldtype": "Date", "width": 110},
        {
            "label": _("Days Until Unit Is Free"),
            "fieldname": "days_until_free",
            "fieldtype": "Int",
            "width": 170,
        },
    ]


def get_data(filters):
    where = ["1=1"]
    args = {}

    if filters.get("property"):
        where.append("pu.property = %(property)s")
        args["property"] = filters.get("property")

    if filters.get("unit"):
        where.append("pu.name = %(unit)s")
        args["unit"] = filters.get("unit")

    if filters.get("property_type"):
        where.append("p.property_type = %(property_type)s")
        args["property_type"] = filters.get("property_type")

    if filters.get("tenant"):
        where.append("(la.customer = %(tenant)s OR pu.tenant = %(tenant)s OR pu.current_tenant = %(tenant)s)")
        args["tenant"] = filters.get("tenant")

    rows = frappe.db.sql(
        """
        SELECT
            pu.name AS unit,
            pu.property,
            pu.status AS unit_status,
            p.property_type,
            la.name AS lease_agreement,
            COALESCE(la.customer, pu.tenant, pu.current_tenant) AS tenant,
            la.contract_type,
            la.end_date,
            la.status AS lease_status
        FROM `tabProperty Unit` pu
        LEFT JOIN `tabProperty` p ON p.name = pu.property
        LEFT JOIN `tabLease Agreement` la ON la.name = (
            SELECT la2.name
            FROM `tabLease Agreement` la2
            WHERE la2.unit = pu.name
              AND la2.docstatus = 1
              AND la2.status NOT IN ('Cancelled', 'Finished', 'Expired')
            ORDER BY la2.start_date DESC, la2.creation DESC
            LIMIT 1
        )
        WHERE {where}
        ORDER BY pu.property, pu.name
        """.format(where=" AND ".join(where)),
        args,
        as_dict=True,
    )

    today_date = getdate(today())
    seen = set()
    data = []

    for row in rows:
        key = (row.unit, row.lease_agreement or "")
        if key in seen:
            continue
        seen.add(key)

        if row.unit_status in ("Available", "Under Maintenance", "Vacant"):
            row.days_until_free = 0
        elif not row.lease_agreement:
            row.days_until_free = None
        elif row.end_date:
            row.days_until_free = max(date_diff(getdate(row.end_date), today_date), 0)
        else:
            row.days_until_free = None

        data.append(row)

    return data
