# -*- coding: utf-8 -*-
# Copyright (c) 2018, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class Property(NestedSet):
    nsm_parent_field = "parent_property"

    def before_insert(self):
        if not self.name1 and self.name:
            self.name1 = self.name

    def validate(self):
        if self.name and not self.name1:
            self.name1 = self.name
        self.validate_property_owner()
        self.validate_disabled_transition()

    def validate_property_owner(self):
        """Prevent the 'Could not find Owner: Administrator' error.

        Frappe's Link validation throws when the value of the field labelled
        'Owner' is not a valid Customer. Some forms accidentally pass the
        document's `owner` system field (which holds a User like
        'Administrator') as the property_owner. Clear the value if it doesn't
        resolve to a Customer.
        """
        if self.property_owner and not frappe.db.exists("Customer", self.property_owner):
            frappe.msgprint(
                _(
                    "Owner '{0}' is not a Customer. "
                    "Cleared - select an existing Customer or leave it blank."
                ).format(self.property_owner),
                indicator="orange",
                alert=True,
            )
            self.property_owner = None

        if self.unit_owner and not frappe.db.exists("Customer", self.unit_owner):
            self.unit_owner = None

    def validate_disabled_transition(self):
        if not self.disabled:
            return

        previous = self.get_doc_before_save()
        was_disabled = previous and previous.disabled
        if was_disabled:
            return

        active_lease_count = frappe.db.count(
            "Lease Agreement",
            filters={"property": self.name, "status": ("in", ("Active", "Draft"))},
        )
        if active_lease_count:
            frappe.throw(
                _(
                    "Cannot disable property '{0}' - there are {1} active or draft "
                    "lease(s). Cancel them first."
                ).format(self.name, active_lease_count)
            )

    def on_trash(self, allow_root_deletion=True):
        super().on_trash(allow_root_deletion)


@frappe.whitelist()
def add_node():
    from frappe.desk.treeview import make_tree_args

    args = make_tree_args(**frappe.form_dict)

    if args["is_root"]:
        args["parent_property"] = None

    args.pop("owner", None)

    doc = frappe.get_doc(args)

    doc.save()


@frappe.whitelist()
def get_active_leases(property_name):
    return frappe.get_all(
        "Lease Agreement",
        filters={"property": property_name, "status": ("in", ("Active", "Draft"))},
        fields=["name", "customer", "unit", "start_date", "end_date", "status"],
    )
