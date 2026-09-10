# -*- coding: utf-8 -*-
"""Deactivate Lease Agreement workflow so Save & Submit is used directly."""

from __future__ import unicode_literals

import frappe


def execute():
    for name in frappe.get_all(
        "Workflow",
        filters={"document_type": "Lease Agreement", "is_active": 1},
        pluck="name",
    ):
        frappe.db.set_value("Workflow", name, "is_active", 0)

    frappe.clear_cache(doctype="Lease Agreement")
