# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Property", "width": 180},
        {"label": _("Property Type"), "fieldname": "property_type", "fieldtype": "Link", "options": "Property Type", "width": 120},
        {"label": _("Units"), "fieldname": "unit_count", "fieldtype": "Int", "width": 80},
        {"label": _("Active Leases"), "fieldname": "lease_count", "fieldtype": "Int", "width": 100},
        {"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 140},
        {
            "label": _("Maintenance Cost (Purchase Inv.)"),
            "fieldname": "maintenance_cost",
            "fieldtype": "Currency",
            "width": 200,
        },
        {"label": _("Net"), "fieldname": "net", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    property_filter = ""
    cond_args = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "company": filters.get("company"),
    }

    if filters.get("property"):
        property_filter = "AND p.name = %(property)s"
        cond_args["property"] = filters.get("property")

    properties = frappe.db.sql(
        """
        SELECT p.name AS property, p.property_type AS property_type, p.company AS company
        FROM `tabProperty` p
        WHERE (%(company)s IS NULL OR %(company)s = '' OR p.company = %(company)s)
        {property_filter}
        ORDER BY p.name
        """.format(property_filter=property_filter),
        cond_args,
        as_dict=True,
    )

    rows = []
    for prop in properties:
        unit_count = _get_unit_count(prop.property, filters)
        lease_count = _get_active_lease_count(prop.property, filters)
        revenue = _get_revenue(prop.property, filters)
        maintenance_cost = _get_maintenance_cost(prop.property, filters)
        rows.append(
            {
                "property": prop.property,
                "property_type": prop.property_type,
                "unit_count": unit_count,
                "lease_count": lease_count,
                "revenue": revenue,
                "maintenance_cost": maintenance_cost,
                "net": (revenue or 0) - (maintenance_cost or 0),
            }
        )
    return rows


def _get_unit_count(property_name, filters):
    f = {"property": property_name}
    if filters.get("unit"):
        f["name"] = filters.get("unit")
    return frappe.db.count("Unit Master", filters=f)


def _get_active_lease_count(property_name, filters):
    f = {"property": property_name, "status": ("in", ("Active", "Draft"))}
    if filters.get("tenant"):
        f["customer"] = filters.get("tenant")
    if filters.get("unit"):
        f["unit"] = filters.get("unit")
    return frappe.db.count("Lease Agreement", filters=f)


def _get_revenue(property_name, filters):
    """Sum of paid Sales Invoices for units belonging to this property."""
    extra = []
    args = {
        "property": property_name,
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }
    if filters.get("unit"):
        extra.append("AND la.unit = %(unit)s")
        args["unit"] = filters.get("unit")
    if filters.get("tenant"):
        extra.append("AND si.customer = %(tenant)s")
        args["tenant"] = filters.get("tenant")

    extra_sql = " ".join(extra)
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(si.grand_total), 0)
        FROM `tabSales Invoice` si
        INNER JOIN `tabLease Agreement Invoice Schedule` lais
            ON lais.sales_invoice = si.name
        INNER JOIN `tabLease Agreement` la
            ON la.name = lais.parent
        WHERE si.docstatus = 1
          AND la.property = %(property)s
          AND (%(from_date)s IS NULL OR si.posting_date >= %(from_date)s)
          AND (%(to_date)s IS NULL OR si.posting_date <= %(to_date)s)
          {extra_sql}
        """.format(extra_sql=extra_sql),
        args,
    )
    return float(result[0][0]) if result and result[0] else 0


def _get_maintenance_cost(property_name, filters):
    """Maintenance cost is sourced from Purchase Invoices linked to maintenance.

    A Purchase Invoice can be linked via the custom fields propms_property
    (or via a Maintenance Request in propms_maintenance_request).
    """
    extra = []
    args = {
        "property": property_name,
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }
    if filters.get("unit"):
        extra.append("AND pi.propms_unit = %(unit)s")
        args["unit"] = filters.get("unit")

    extra_sql = " ".join(extra)
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(pi.grand_total), 0)
        FROM `tabPurchase Invoice` pi
        WHERE pi.docstatus = 1
          AND pi.propms_property = %(property)s
          AND (%(from_date)s IS NULL OR pi.posting_date >= %(from_date)s)
          AND (%(to_date)s IS NULL OR pi.posting_date <= %(to_date)s)
          {extra_sql}
        """.format(extra_sql=extra_sql),
        args,
    )
    return float(result[0][0]) if result and result[0] else 0
