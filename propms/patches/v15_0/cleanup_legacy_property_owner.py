# -*- coding: utf-8 -*-
"""Clear Property.property_owner / unit_owner values that point to a User.

Previously some sites had `property_owner = 'Administrator'` (a User) which
makes Frappe throw "Could not find Owner: Administrator" because the field is
a Link to Customer. This patch resets such invalid values to NULL so the
affected Property records can be saved again.
"""

from __future__ import unicode_literals

import frappe


def execute():
    if not frappe.db.has_column("Property", "property_owner"):
        return

    invalid_property_owners = frappe.db.sql(
        """
        SELECT name, property_owner FROM `tabProperty`
        WHERE property_owner IS NOT NULL
          AND property_owner != ''
          AND property_owner NOT IN (SELECT name FROM `tabCustomer`)
        """,
        as_dict=True,
    )
    for row in invalid_property_owners:
        frappe.db.set_value("Property", row.name, "property_owner", None)

    if frappe.db.has_column("Property", "unit_owner"):
        invalid_unit_owners = frappe.db.sql(
            """
            SELECT name, unit_owner FROM `tabProperty`
            WHERE unit_owner IS NOT NULL
              AND unit_owner != ''
              AND unit_owner NOT IN (SELECT name FROM `tabCustomer`)
            """,
            as_dict=True,
        )
        for row in invalid_unit_owners:
            frappe.db.set_value("Property", row.name, "unit_owner", None)

    frappe.db.commit()
