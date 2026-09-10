# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import os

import frappe
from frappe.modules.import_file import import_file_by_path

WORKSPACE_NAME = "Property Lifecycle Dashboard"


def sync_property_lifecycle_dashboard():
	"""Re-import the Property Lifecycle workspace from shipped JSON (no rebuild)."""
	_import_number_cards()
	_import_workspace_json()
	_remove_leased_units_card()
	frappe.clear_cache()


def _remove_leased_units_card():
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return
	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False
	for row in list(workspace.number_cards):
		if row.number_card_name == "Leased Units":
			workspace.number_cards.remove(row)
			changed = True
	if workspace.content and "Leased Units" in workspace.content:
		import json

		content = json.loads(workspace.content)
		content = [
			block
			for block in content
			if not (
				block.get("type") == "number_card"
				and block.get("data", {}).get("number_card_name") == "Leased Units"
			)
		]
		workspace.content = json.dumps(content, ensure_ascii=False)
		changed = True
	if changed:
		workspace.save(ignore_permissions=True)


def _import_number_cards():
	base = frappe.get_app_path("propms", "property_management_solution")
	slugs = (
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
	for slug in slugs:
		path = os.path.join(base, "number_card", slug, "{}.json".format(slug))
		if os.path.isfile(path):
			import_file_by_path(path, force=True)


def _import_workspace_json():
	path = os.path.join(
		frappe.get_app_path("propms", "property_management_solution"),
		"workspace",
		"real_estate_management",
		"real_estate_management.json",
	)
	if os.path.isfile(path):
		import_file_by_path(path, force=True)
