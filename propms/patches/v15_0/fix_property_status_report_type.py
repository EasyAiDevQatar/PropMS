import os

import frappe
from frappe.modules.import_file import import_file_by_path


def execute():
	"""Replace legacy Query Report SQL for Property Status with the propms Script Report."""
	path = os.path.join(
		frappe.get_app_path("propms", "property_management_solution"),
		"report",
		"property_status",
		"property_status.json",
	)
	if os.path.isfile(path):
		import_file_by_path(path, force=True)
