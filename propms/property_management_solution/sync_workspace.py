# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import json
import os

import frappe
from frappe.modules.import_file import import_file_by_path

WORKSPACE_NAME = "Property Lifecycle Dashboard"

ALLOWED_CARDS = (
	"Master Data",
	"Leasing Operations",
	"Billing & Collections",
	"Maintenance Operations",
	"CRM & Sales",
	"Reports & Analytics",
	"Settings",
)


def sync_property_lifecycle_dashboard():
	"""Re-import the Property Lifecycle workspace from shipped JSON (no rebuild)."""
	_import_workspace_json()
	_strip_dashboard_blocks()
	frappe.clear_cache()


def _strip_dashboard_blocks():
	"""Keep Workflow Sections cards only — drop metrics / quick actions if present."""
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return
	workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False
	if workspace.number_cards:
		workspace.set("number_cards", [])
		changed = True
	if workspace.shortcuts:
		workspace.set("shortcuts", [])
		changed = True
	if workspace.charts:
		workspace.set("charts", [])
		changed = True
	if workspace.content:
		content = json.loads(workspace.content)
		new_content = []
		has_header = False
		for block in content:
			btype = block.get("type")
			data = block.get("data") or {}
			if btype in ("number_card", "shortcut", "chart", "paragraph", "spacer"):
				changed = True
				continue
			if btype == "card":
				name = data.get("card_name")
				if name not in ALLOWED_CARDS:
					changed = True
					continue
				data = dict(data)
				data["col"] = 4
				block = dict(block)
				block["data"] = data
				new_content.append(block)
				continue
			if btype == "header":
				text = data.get("text") or ""
				if "Workflow Sections" in text:
					has_header = True
					new_content.append(block)
				else:
					changed = True
				continue
			new_content.append(block)
		if not has_header:
			new_content.insert(
				0,
				{
					"type": "header",
					"data": {
						"text": '<span class="h4"><b>Workflow Sections</b></span>',
						"col": 12,
					},
				},
			)
			changed = True
		workspace.content = json.dumps(new_content, ensure_ascii=False)
	if changed:
		workspace.save(ignore_permissions=True)


def _import_workspace_json():
	path = os.path.join(
		frappe.get_app_path("propms", "property_management_solution"),
		"workspace",
		"real_estate_management",
		"real_estate_management.json",
	)
	if os.path.isfile(path):
		import_file_by_path(path, force=True)
