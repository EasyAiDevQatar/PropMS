# -*- coding: utf-8 -*-
"""Import all dashboard number cards and Property Lifecycle workspace."""

from __future__ import unicode_literals

import os

import frappe
from frappe.modules.import_file import import_file_by_path


NUMBER_CARDS = (
	"monthly_revenue",
	"monthly_expenses",
	"unpaid_invoices",
	"total_collections",
	"outstanding_amounts",
	"maintenance_cost",
	"total_properties",
	"total_units",
	"available_units",
	"occupied_units",
	"sold_units",
	"active_contracts",
	"expired_contracts",
	"expiring_contracts_30d",
	"expiring_contracts",
	"total_leads",
	"total_opportunities",
	"property_viewings",
	"total_commissions",
)

DEFAULT_VIEWING_STATUSES = (
	("Scheduled", "Blue"),
	("Completed", "Green"),
	("Cancelled", "Red"),
	("Rescheduled", "Orange"),
	("No Show", "Grey"),
	("Interested", "Purple"),
)


def execute():
	from propms.property_management_solution.sync_workspace import sync_property_lifecycle_dashboard

	sync_property_lifecycle_dashboard()

	for workspace_name in (
		"Property MS",
		"Real Estate Management",
		"Property Operations Center",
		"Property Management",
	):
		if frappe.db.exists("Workspace", workspace_name):
			frappe.delete_doc("Workspace", workspace_name, force=True, ignore_permissions=True)

	_ensure_viewing_statuses()
	frappe.clear_cache()


def _ensure_viewing_statuses():
	if not frappe.db.table_exists("tabViewing Status"):
		return
	for status, color in DEFAULT_VIEWING_STATUSES:
		if frappe.db.exists("Viewing Status", status):
			continue
		frappe.get_doc(
			{"doctype": "Viewing Status", "status": status, "color": color}
		).insert(ignore_permissions=True)
