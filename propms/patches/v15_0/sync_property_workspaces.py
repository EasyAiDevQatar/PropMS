# -*- coding: utf-8 -*-
"""Re-import Property MS and Real Estate Management workspaces from module JSON.

Desk reads Workspace from the database. Editing workspace JSON in the app does not
update existing sites until the document is re-imported (or reset from Customize).
This patch runs once per site so link cards and shortcuts match the shipped JSON.
"""

from __future__ import unicode_literals

import os

import frappe
from frappe.modules.import_file import import_file_by_path


def execute():
	base = frappe.get_app_path("propms", "property_management_solution")
	path = os.path.join(base, "workspace", "real_estate_management", "real_estate_management.json")
	if os.path.isfile(path):
		import_file_by_path(path, force=True)
	if frappe.db.exists("Workspace", "Real Estate Management"):
		frappe.delete_doc("Workspace", "Real Estate Management", force=True, ignore_permissions=True)
	frappe.clear_cache()
