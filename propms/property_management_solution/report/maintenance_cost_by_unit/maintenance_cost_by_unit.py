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
			"width": 160,
		},
		{"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Property", "width": 160},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Link", "options": "Unit Master", "width": 130},
		{
			"label": _("Journal Entry"),
			"fieldname": "journal_entry",
			"fieldtype": "Link",
			"options": "Journal Entry",
			"width": 150,
		},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Request Date"), "fieldname": "request_date", "fieldtype": "Date", "width": 110},
		{"label": _("JE Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = [
		"mr.docstatus = 1",
		"mr.journal_entry IS NOT NULL",
		"mr.journal_entry != ''",
		"mr.unit IS NOT NULL",
		"mr.unit != ''",
		"je.docstatus = 1",
	]
	values = {}

	if filters.get("property"):
		conditions.append("mr.property = %(property)s")
		values["property"] = filters["property"]
	if filters.get("unit"):
		conditions.append("mr.unit = %(unit)s")
		values["unit"] = filters["unit"]
	if filters.get("from_date"):
		conditions.append("je.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("je.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		SELECT
			mr.name,
			mr.property,
			mr.unit,
			mr.journal_entry,
			mr.status,
			mr.request_date,
			je.posting_date,
			COALESCE(NULLIF(mr.total_cost, 0), mr.cost, mr.total_amount, 0) AS total_cost
		FROM `tabMaintenance Request` mr
		INNER JOIN `tabJournal Entry` je ON je.name = mr.journal_entry
		WHERE {where}
		ORDER BY mr.unit ASC, je.posting_date DESC, mr.name DESC
		""".format(where=" AND ".join(conditions)),
		values,
		as_dict=True,
	)
