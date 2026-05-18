# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import frappe


def execute():
    create_records(
        "Property Type",
        "property_type",
        ["Building", "Villa", "Land", "Office", "Apartment"],
    )
    create_records("Unit Type", "unit_type", ["Apartment", "Shop", "Office", "Room"])


def create_records(doctype, fieldname, values):
    for value in values:
        if frappe.db.exists(doctype, value):
            continue

        doc = frappe.get_doc({"doctype": doctype, fieldname: value})
        doc.insert(ignore_permissions=True)
