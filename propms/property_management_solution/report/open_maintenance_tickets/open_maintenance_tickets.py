# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Maintenance Request"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Maintenance Request",
			"width": 150,
		},
		{"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Property", "width": 140},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Unit Master", "width": 130},
		{"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "options": "Customer", "width": 140},
		{"label": _("Issue Type"), "fieldname": "issue_type", "fieldtype": "Link", "options": "Issue Type", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Request Date"), "fieldname": "request_date", "fieldtype": "Date", "width": 110},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = {"status": ("in", ("Open", "In Progress", "On Hold"))}
	if filters.get("property"):
		conditions["property"] = filters["property"]
	if filters.get("unit"):
		conditions["unit"] = filters["unit"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["request_date"] = ["between", [filters["from_date"], filters["to_date"]]]

	return frappe.get_all(
		"Maintenance Request",
		filters=conditions,
		fields=[
			"name",
			"property",
			"unit",
			"tenant",
			"issue_type",
			"status",
			"request_date",
			"total_cost",
		],
		order_by="request_date desc",
	)
