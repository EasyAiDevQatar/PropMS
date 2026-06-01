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
	for fname in ("real_estate_management", "property_ms"):
		path = os.path.join(base, "workspace", fname, "{}.json".format(fname))
		if os.path.isfile(path):
			import_file_by_path(path, force=True)
	frappe.clear_cache()
