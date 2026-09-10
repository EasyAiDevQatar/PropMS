import os

import frappe
from frappe.modules.import_file import import_file_by_path


def execute():
	"""Enable total rows on all Property Management Solution reports."""
	base = frappe.get_app_path("propms", "property_management_solution", "report")
	for name in sorted(os.listdir(base)):
		path = os.path.join(base, name, f"{name}.json")
		if os.path.isfile(path):
			import_file_by_path(path, force=True)

	frappe.db.sql(
		"""
		UPDATE `tabReport`
		SET add_total_row = 1
		WHERE module = 'Property Management Solution'
		  AND COALESCE(add_total_row, 0) = 0
		"""
	)
