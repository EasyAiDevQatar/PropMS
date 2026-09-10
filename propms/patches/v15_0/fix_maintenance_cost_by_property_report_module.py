import frappe

REPORTS = ("Maintenance Cost By Property", "Maintenance Cost By Unit")


def execute():
	"""Point maintenance cost reports at propms, not payments."""
	for report_name in REPORTS:
		if not frappe.db.exists("Report", report_name):
			continue

		module = frappe.db.get_value("Report", report_name, "module")
		if module == "Property Management Solution":
			continue

		frappe.db.set_value(
			"Report",
			report_name,
			"module",
			"Property Management Solution",
			update_modified=False,
		)
