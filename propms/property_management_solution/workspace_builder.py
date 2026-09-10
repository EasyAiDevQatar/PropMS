# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import json
import os

MODULE = "Property Management Solution"
SETTINGS_DOCTYPE = "Property Management Settings"
REPORTS_SECTION = "Reports & Analytics"

QUERY_REPORT_TYPES = ("Query Report", "Script Report", "Custom Report")

QUICK_ACTIONS = (
	("New Property", "Property", "DocType", "List"),
	("New Unit", "Unit Master", "DocType", "List"),
	("New Tenant", "Customer", "DocType", "List"),
	("New Lease Agreement", "Lease Agreement", "DocType", "List"),
	("New Lease Invoice", "Sales Invoice", "DocType", "List"),
	("Record Lease Payment", "Payment Entry", "DocType", "List"),
	("New Maintenance Request", "Maintenance Request", "DocType", "List"),
	("New Property Viewing", "Property Viewing", "DocType", "List"),
	(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE, "DocType", "Form"),
)

RELATED_DOCTYPES = (
	"Customer",
	"Contract",
	"Sales Invoice",
	"Payment Entry",
	"Journal Entry",
	"Purchase Invoice",
	"Issue",
	"Lead",
	"Opportunity",
	"Quotation",
	"Material Request",
	"Issue Type",
)

SECTION_DOCTYPES = {
	"Master Data": (
		"Property Type",
		"Unit Type",
		"Viewing Status",
		"Charges Setup",
		"Issue Type",
		"Apartment Status",
		"Property",
		"Unit Master",
		"Customer",
		"Property Viewing",
		"Property Management Settings",
	),
	"Leasing Operations": (
		"Lease Agreement",
		"Lease",
		"Contract",
		"Security Deposit Details",
		"Insurance",
	),
	"Billing & Collections": (
		"Sales Invoice",
		"Payment Entry",
		"Journal Entry",
		"Purchase Invoice",
	),
	"Maintenance Operations": (
		"Maintenance Request",
		"Tool Item Set",
		"Tool Item Record",
		"Issue",
	),
	"Security & Facility Operations": (
		"Security Attendance",
		"Guard Shift",
		"Outsourcing Category",
		"Outsourcing Shift",
		"Outsourcing Attendance",
		"Daily Checklist",
		"Checklist Checkup Area",
		"Key Set",
		"Key Set Detail",
		"Meter",
		"Meter Reading",
		"Exit",
		"Custom Error Log",
	),
	"CRM & Sales": (
		"Lead",
		"Opportunity",
		"Quotation",
	),
}

NUMBER_CARDS = (
	"Total Properties",
	"Total Units",
	"Available Units",
	"Occupied Units",
	"Sold Units",
	"Active Contracts",
	"Expired Contracts",
	"Expiring Contracts (30D)",
	"Expiring Contracts (120D)",
	"Monthly Revenue",
	"Monthly Expenses",
	"Unpaid Invoices",
	"Total Collections",
	"Outstanding Amounts",
	"Maintenance Cost",
	"Total Commissions",
	"Property Viewings",
	"Total Leads",
	"Total Opportunities",
)


def discover_module_doctypes(app_path=None):
	app_path = app_path or _module_base_path()
	standalone, child = [], []

	for path in _sorted_glob(os.path.join(app_path, "doctype", "*", "*.json")):
		with open(path) as handle:
			doc = json.load(handle)
		if doc.get("module") != MODULE:
			continue
		name = doc.get("name")
		if not name:
			continue
		(child if doc.get("istable") else standalone).append(name)

	return sorted(standalone), sorted(child)


def discover_module_reports(app_path=None):
	"""Return report metadata dicts keyed by report name."""
	app_path = app_path or _module_base_path()
	reports = {}
	for path in _sorted_glob(os.path.join(app_path, "report", "*", "*.json")):
		with open(path) as handle:
			doc = json.load(handle)
		if doc.get("module") != MODULE or not doc.get("name"):
			continue
		name = doc.get("name")
		if not name:
			continue
		reports[name] = {
			"name": name,
			"report_type": doc.get("report_type") or "Report Builder",
			"ref_doctype": doc.get("ref_doctype"),
		}
	return reports


def build_workspace_dict(existing=None):
	existing = existing or {}
	standalone, child = discover_module_doctypes()
	reports = discover_module_reports()

	sections = _build_sections(standalone, child, reports)
	links = _build_links(sections, reports)
	shortcuts = _build_shortcuts(sections)
	content = _build_content(sections)

	return {
		"charts": existing.get("charts") or [],
		"content": json.dumps(content, ensure_ascii=False),
		"creation": existing.get("creation") or "2020-12-28 17:56:01.070160",
		"docstatus": 0,
		"doctype": "Workspace",
		"hide_custom": 0,
		"icon": "dashboard",
		"idx": 0,
		"indicator_color": "purple",
		"is_hidden": 0,
		"label": "Property Lifecycle Dashboard",
		"links": links,
		"modified": existing.get("modified") or "2026-06-21 00:00:00.000000",
		"modified_by": "Administrator",
		"module": MODULE,
		"name": "Property Lifecycle Dashboard",
		"number_cards": [{"label": name, "number_card_name": name} for name in NUMBER_CARDS],
		"owner": "Administrator",
		"public": 1,
		"quick_lists": [],
		"roles": existing.get("roles")
		or [
			{"role": "System Manager"},
			{"role": "Property Manager"},
			{"role": "Accounts User"},
		],
		"sequence_id": existing.get("sequence_id") or 374.0,
		"shortcuts": shortcuts,
		"title": "Property Lifecycle Dashboard",
	}


def write_workspace_json(path=None):
	path = path or os.path.join(
		_module_base_path(),
		"workspace",
		"real_estate_management",
		"real_estate_management.json",
	)
	existing = {}
	if os.path.isfile(path):
		with open(path) as handle:
			existing = json.load(handle)
	doc = build_workspace_dict(existing)
	with open(path, "w") as handle:
		json.dump(doc, handle, indent=1, ensure_ascii=False)
		handle.write("\n")
	return path


def _module_base_path():
	try:
		import frappe

		return frappe.get_app_path("propms", "property_management_solution")
	except Exception:
		return os.path.dirname(os.path.abspath(__file__))


def _sorted_glob(pattern):
	return sorted(glob for glob in __import__("glob").glob(pattern) if os.path.isfile(glob))


def _build_sections(standalone, child, reports):
	assigned = set()
	sections = []

	for title, names in SECTION_DOCTYPES.items():
		items = []
		for name in names:
			if name in assigned:
				continue
			if name in standalone or name in RELATED_DOCTYPES:
				items.append((name, "DocType"))
				assigned.add(name)
		if items:
			sections.append((title, items))

	remaining = [name for name in standalone if name not in assigned]
	if remaining:
		for idx, (title, items) in enumerate(sections):
			if title == "Master Data":
				sections[idx] = (title, [(name, "DocType") for name in remaining] + items)
				assigned.update(remaining)
				break
		else:
			sections.insert(0, ("Master Data", [(name, "DocType") for name in remaining]))
			assigned.update(remaining)

	if child:
		sections.append(("Child DocTypes", [(name, "DocType") for name in child]))

	if reports:
		report_items = [(name, "Report") for name in sorted(reports)]
		sections.append((REPORTS_SECTION, report_items))

	if SETTINGS_DOCTYPE not in assigned:
		sections.append(("Settings", [(SETTINGS_DOCTYPE, "DocType")]))

	return sections


def _build_links(sections, reports):
	links = []
	for section_name, items in sections:
		links.append(_card_break(section_name))
		seen = set()
		for label, link_type in items:
			if label in seen:
				continue
			seen.add(label)
			if link_type == "Report":
				links.append(_report_link(reports[label]))
			else:
				links.append(_link(label, label, "DocType"))
	return links


def _build_shortcuts(sections):
	"""DocType shortcuts only — reports use workspace link cards for correct routing."""
	shortcuts = []
	for label, link_to, link_type, doc_view in QUICK_ACTIONS:
		entry = {"color": "Grey", "label": label, "link_to": link_to, "type": link_type}
		if link_type == "DocType":
			entry["doc_view"] = doc_view
		shortcuts.append(entry)

	used_labels = {item[0] for item in QUICK_ACTIONS}
	for section_name, items in sections:
		if section_name == REPORTS_SECTION:
			continue
		for label, link_type in items:
			if link_type != "DocType" or label in used_labels:
				continue
			shortcuts.append(
				{
					"color": "Grey",
					"label": label,
					"link_to": label,
					"type": "DocType",
					"doc_view": "List",
				}
			)
			used_labels.add(label)
	return shortcuts


def _build_content(sections):
	content = [
		{"type": "header", "data": {"text": '<span class="h4">Property Lifecycle Dashboard</span>', "col": 12}},
		{
			"type": "paragraph",
			"data": {
				"text": "Complete Property Management Solution — masters, operations, billing, maintenance, and reports.",
				"col": 12,
			},
		},
		{"type": "spacer", "data": {"col": 12}},
		{"type": "header", "data": {"text": '<span class="h4"><b>Quick Actions</b></span>', "col": 12}},
	]
	for label, _link_to, _link_type, _doc_view in QUICK_ACTIONS:
		content.append({"type": "shortcut", "data": {"shortcut_name": label, "col": 3}})

	content.extend(
		[
			{"type": "spacer", "data": {"col": 12}},
			{"type": "header", "data": {"text": '<span class="h4"><b>Key Metrics</b></span>', "col": 12}},
		]
	)
	for name in NUMBER_CARDS:
		content.append({"type": "number_card", "data": {"number_card_name": name, "col": 4}})

	content.extend(
		[
			{"type": "spacer", "data": {"col": 12}},
			{"type": "header", "data": {"text": '<span class="h4"><b>Property Management Solution</b></span>', "col": 12}},
			{
				"type": "paragraph",
				"data": {
					"text": "DocTypes grouped by area below. Reports open from the Reports & Analytics link list.",
					"col": 12,
				},
			},
		]
	)

	for section_name, items in sections:
		content.append({"type": "spacer", "data": {"col": 12}})
		content.append(
			{"type": "header", "data": {"text": '<span class="h5"><b>{}</b></span>'.format(section_name), "col": 12}}
		)

		if section_name == REPORTS_SECTION:
			# Frappe link cards route Script/Query/Report Builder reports correctly.
			content.append({"type": "card", "data": {"card_name": REPORTS_SECTION, "col": 12}})
			continue

		seen = set()
		for label, link_type in items:
			if link_type != "DocType" or label in seen:
				continue
			seen.add(label)
			content.append({"type": "shortcut", "data": {"shortcut_name": label, "col": 3}})

	return content


def _card_break(label):
	return {
		"hidden": 0,
		"is_query_report": 0,
		"label": label,
		"link_type": "DocType",
		"onboard": 0,
		"type": "Card Break",
	}


def _link(label, link_to, link_type="DocType"):
	return {
		"hidden": 0,
		"is_query_report": 0,
		"label": label,
		"link_to": link_to,
		"link_type": link_type,
		"onboard": 0,
		"type": "Link",
	}


def _report_link(report):
	is_query_report = report.get("report_type") in QUERY_REPORT_TYPES
	link = {
		"hidden": 0,
		"is_query_report": 1 if is_query_report else 0,
		"label": report["name"],
		"link_to": report["name"],
		"link_type": "Report",
		"onboard": 0,
		"type": "Link",
	}
	ref_doctype = report.get("ref_doctype")
	if ref_doctype:
		link["report_ref_doctype"] = ref_doctype
		if not is_query_report:
			link["dependencies"] = ref_doctype
	return link
