# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import frappe
from frappe.utils import flt, get_first_day, get_last_day, getdate, today


def _month_bounds():
	posting_date = getdate(today())
	return get_first_day(posting_date), get_last_day(posting_date)


def _company_filter(company=None):
	company = company or frappe.defaults.get_user_default("Company")
	return company


def _company_currency():
	return frappe.db.get_default("currency") or frappe.get_cached_value(
		"Company", _company_filter(), "default_currency"
	) or "QAR"


def _currency_result(value, doctype=None, route_options=None, report_name=None):
	result = {
		"value": flt(value),
		"fieldtype": "Currency",
		"options": _company_currency(),
	}
	if report_name:
		result["route"] = ["query-report", report_name]
	elif doctype:
		result["route"] = ["List", doctype]
	if route_options:
		result["route_options"] = route_options
	return result


def _count_result(value, doctype, route_options=None, report_name=None):
	result = {"value": value}
	if report_name:
		result["route"] = ["query-report", report_name]
	elif doctype:
		result["route"] = ["List", doctype]
	if route_options:
		result["route_options"] = route_options
	return result


def _route_filter(doctype, field, operator, value):
	return {f"{doctype}.{field}": [operator, value]}


def _month_route_filters(doctype, date_field="posting_date"):
	start, end = _month_bounds()
	return {
		f"{doctype}.{date_field}": ["between", [start, end]],
		f"{doctype}.docstatus": ["=", 1],
	}


def _units_meta():
	"""Use Unit Master when populated; otherwise Property Unit (legacy live data)."""
	if frappe.db.count("Unit Master"):
		return {
			"doctype": "Unit Master",
			"available": "Available",
			"occupied": "Rented",
			"sold": "Sold",
		}
	return {
		"doctype": "Property Unit",
		"available": "Available",
		"occupied": "Occupied",
		"sold": "Sold",
	}


def _count_units(filters=None):
	meta = _units_meta()
	return frappe.db.count(meta["doctype"], filters or {})


def _lease_contract_doctype():
	if frappe.db.count("Lease Contract"):
		return "Lease Contract"
	if frappe.db.count("Lease Agreement"):
		return "Lease Agreement"
	return "Lease Contract"


def _active_contract_filters():
	if _lease_contract_doctype() == "Lease Contract":
		return {"docstatus": 1, "status": ("in", ("Active", "Approved"))}
	return {"docstatus": 1, "status": ("in", ("Active", "Draft"))}


def _lease_si_exists_sql(alias="si"):
	"""SQL fragment: sales invoice linked to a lease contract/agreement."""
	return """
		(
			({alias}.pm_lease_contract IS NOT NULL AND {alias}.pm_lease_contract != '')
			OR ({alias}.propms_lease_agreement IS NOT NULL AND {alias}.propms_lease_agreement != '')
			OR ({alias}.lease IS NOT NULL AND {alias}.lease != '')
			OR EXISTS (
				SELECT 1 FROM `tabLease Agreement Invoice Schedule` lais
				WHERE lais.sales_invoice = {alias}.name
			)
		)
	""".format(alias=alias)


def _lease_pe_exists_sql(alias="pe"):
	"""SQL fragment: payment entry linked to a lease contract/agreement."""
	return """
		(
			({alias}.pm_lease_contract IS NOT NULL AND {alias}.pm_lease_contract != '')
			OR ({alias}.propms_lease_agreement IS NOT NULL AND {alias}.propms_lease_agreement != '')
		)
	""".format(alias=alias)


@frappe.whitelist()
def get_monthly_revenue():
	"""Submitted lease-linked Sales Invoice amount for the current month."""
	start, end = _month_bounds()
	company = _company_filter()
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(si.grand_total), 0)
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		  AND si.posting_date BETWEEN %(start)s AND %(end)s
		  AND (%(company)s IS NULL OR %(company)s = '' OR si.company = %(company)s)
		  AND {lease_si}
		""".format(lease_si=_lease_si_exists_sql("si")),
		{"start": start, "end": end, "company": company},
	)
	return _currency_result(
		result[0][0] if result and result[0] else 0,
		"Sales Invoice",
		_month_route_filters("Sales Invoice"),
	)


@frappe.whitelist()
def get_monthly_expenses():
	"""Submitted maintenance request cost (with linked journal entry) for the current month."""
	start, end = _month_bounds()
	company = _company_filter()
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(COALESCE(NULLIF(mr.total_cost, 0), mr.cost, mr.total_amount, 0)), 0)
		FROM `tabMaintenance Request` mr
		INNER JOIN `tabJournal Entry` je ON je.name = mr.journal_entry
		WHERE mr.docstatus = 1
		  AND je.docstatus = 1
		  AND mr.journal_entry IS NOT NULL
		  AND mr.journal_entry != ''
		  AND je.posting_date BETWEEN %(start)s AND %(end)s
		  AND (%(company)s IS NULL OR %(company)s = '' OR mr.company = %(company)s)
		""",
		{"start": start, "end": end, "company": company},
	)
	value = result[0][0] if result and result[0] else 0
	return _currency_result(
		value,
		report_name="Maintenance Cost By Property",
		route_options={"from_date": start, "to_date": end},
	)


@frappe.whitelist()
def get_unpaid_invoices():
	"""Outstanding balance on all unpaid lease-linked sales invoices."""
	company = _company_filter()
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(si.outstanding_amount), 0)
		FROM `tabSales Invoice` si
		WHERE si.docstatus = 1
		  AND si.outstanding_amount > 0
		  AND si.status IN ('Unpaid', 'Partly Paid', 'Overdue')
		  AND (%(company)s IS NULL OR %(company)s = '' OR si.company = %(company)s)
		  AND {lease_si}
		""".format(lease_si=_lease_si_exists_sql("si")),
		{"company": company},
	)
	return _currency_result(
		result[0][0] if result and result[0] else 0,
		"Sales Invoice",
		{
			"Sales Invoice.docstatus": ["=", 1],
			"Sales Invoice.outstanding_amount": [">", 0],
			"Sales Invoice.status": ["in", ["Unpaid", "Partly Paid", "Overdue"]],
		},
	)


@frappe.whitelist()
def get_total_collections():
	"""Lease-linked Payment Entry receipts for the current month."""
	start, end = _month_bounds()
	company = _company_filter()
	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(pe.paid_amount), 0)
		FROM `tabPayment Entry` pe
		WHERE pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		  AND pe.posting_date BETWEEN %(start)s AND %(end)s
		  AND (%(company)s IS NULL OR %(company)s = '' OR pe.company = %(company)s)
		  AND {lease_pe}
		""".format(lease_pe=_lease_pe_exists_sql("pe")),
		{"start": start, "end": end, "company": company},
	)
	return _currency_result(
		result[0][0] if result and result[0] else 0,
		"Payment Entry",
		{
			**_month_route_filters("Payment Entry"),
			"Payment Entry.payment_type": ["=", "Receive"],
		},
	)


@frappe.whitelist()
def get_outstanding_amounts():
	return get_unpaid_invoices()


@frappe.whitelist()
def get_maintenance_cost():
	return get_monthly_expenses()


@frappe.whitelist()
def get_total_properties():
	return _count_result(frappe.db.count("Property"), "Property")


@frappe.whitelist()
def get_total_units():
	meta = _units_meta()
	return _count_result(_count_units(), meta["doctype"])


@frappe.whitelist()
def get_available_units():
	meta = _units_meta()
	return _count_result(
		_count_units({"status": meta["available"]}),
		meta["doctype"],
		_route_filter(meta["doctype"], "status", "=", meta["available"]),
	)


@frappe.whitelist()
def get_occupied_units():
	meta = _units_meta()
	return _count_result(
		_count_units({"status": meta["occupied"]}),
		meta["doctype"],
		_route_filter(meta["doctype"], "status", "=", meta["occupied"]),
	)


@frappe.whitelist()
def get_sold_units():
	meta = _units_meta()
	return _count_result(
		_count_units({"status": meta["sold"]}),
		meta["doctype"],
		_route_filter(meta["doctype"], "status", "=", meta["sold"]),
	)


@frappe.whitelist()
def get_leased_units():
	return get_occupied_units()


@frappe.whitelist()
def get_active_contracts():
	doctype = _lease_contract_doctype()
	filters = _active_contract_filters()
	if doctype == "Lease Contract":
		return _count_result(
			frappe.db.count(doctype, filters),
			doctype,
			{
				**_route_filter(doctype, "docstatus", "=", 1),
				**_route_filter(doctype, "status", "in", ["Active", "Approved"]),
			},
		)
	return _count_result(
		frappe.db.count(doctype, filters),
		doctype,
		{
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "in", ["Active", "Draft"]),
		},
	)


@frappe.whitelist()
def get_expired_contracts():
	doctype = _lease_contract_doctype()
	return _count_result(
		frappe.db.count(doctype, {"docstatus": 1, "status": "Expired"}),
		doctype,
		{
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "=", "Expired"),
		},
	)


@frappe.whitelist()
def get_expiring_contracts_30d():
	doctype = _lease_contract_doctype()
	if doctype == "Lease Contract":
		result = frappe.db.sql(
			"""
			SELECT COUNT(name)
			FROM `tabLease Contract`
			WHERE docstatus = 1
			  AND status IN ('Active', 'Approved')
			  AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
			"""
		)
		route_options = {
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "in", ["Active", "Approved"]),
		}
	else:
		result = frappe.db.sql(
			"""
			SELECT COUNT(name)
			FROM `tabLease Agreement`
			WHERE docstatus = 1
			  AND status = 'Active'
			  AND contract_type = 'Rent'
			  AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
			"""
		)
		route_options = {
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "=", "Active"),
		}
	return _count_result(int(result[0][0]) if result and result[0] else 0, doctype, route_options)


@frappe.whitelist()
def get_expiring_contracts():
	doctype = _lease_contract_doctype()
	if doctype == "Lease Contract":
		result = frappe.db.sql(
			"""
			SELECT COUNT(name)
			FROM `tabLease Contract`
			WHERE docstatus = 1
			  AND status IN ('Active', 'Approved')
			  AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 120 DAY)
			"""
		)
		route_options = {
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "in", ["Active", "Approved"]),
		}
	else:
		result = frappe.db.sql(
			"""
			SELECT COUNT(name)
			FROM `tabLease Agreement`
			WHERE docstatus = 1
			  AND status = 'Active'
			  AND contract_type = 'Rent'
			  AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 120 DAY)
			"""
		)
		route_options = {
			**_route_filter(doctype, "docstatus", "=", 1),
			**_route_filter(doctype, "status", "=", "Active"),
		}
	return _count_result(int(result[0][0]) if result and result[0] else 0, doctype, route_options)


@frappe.whitelist()
def get_open_tickets():
	return _count_result(
		frappe.db.count(
			"Maintenance Request",
			{"status": ("in", ("Open", "In Progress", "On Hold"))},
		),
		"Maintenance Request",
		_route_filter("Maintenance Request", "status", "in", ["Open", "In Progress", "On Hold"]),
	)


@frappe.whitelist()
def get_closed_tickets():
	start, end = _month_bounds()
	return _count_result(
		frappe.db.count(
			"Maintenance Request",
			{
				"status": ("in", ("Resolved", "Closed")),
				"request_date": ["between", [start, end]],
			},
		),
		"Maintenance Request",
		{
			**_route_filter("Maintenance Request", "status", "in", ["Resolved", "Closed"]),
			**_route_filter("Maintenance Request", "request_date", "between", [start, end]),
		},
	)


@frappe.whitelist()
def get_total_leads():
	if not frappe.db.exists("DocType", "Lead"):
		return _count_result(0, "Lead")
	return _count_result(frappe.db.count("Lead"), "Lead")


@frappe.whitelist()
def get_total_opportunities():
	if not frappe.db.exists("DocType", "Opportunity"):
		return _count_result(0, "Opportunity")
	return _count_result(
		frappe.db.count("Opportunity"),
		"Opportunity",
		report_name="Opportunities Report",
	)


@frappe.whitelist()
def get_property_viewings():
	if not frappe.db.exists("DocType", "Property Viewing"):
		return _count_result(0, "Property Viewing")
	return _count_result(frappe.db.count("Property Viewing"), "Property Viewing")


@frappe.whitelist()
def get_total_commissions():
	start, end = _month_bounds()
	company = _company_filter()
	if _lease_contract_doctype() == "Lease Contract":
		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(
				CASE
					WHEN contract_type = 'Sale' THEN commission_amount
					WHEN contract_type = 'Rent' THEN commission_amount * rent_commission_factor
					ELSE commission_amount
				END
			), 0)
			FROM `tabLease Contract`
			WHERE docstatus = 1
			  AND start_date BETWEEN %(start)s AND %(end)s
			  AND (%(company)s IS NULL OR %(company)s = '' OR company = %(company)s)
			""",
			{"start": start, "end": end, "company": company},
		)
	else:
		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(
				CASE
					WHEN la.contract_type = 'Sale' THEN la.commission_amount
					WHEN la.contract_type = 'Rent' AND la.rent_commission_only = 1 THEN la.rent_commission_amount
					ELSE 0
				END
			), 0)
			FROM `tabLease Agreement` la
			WHERE la.docstatus = 1
			  AND la.start_date BETWEEN %(start)s AND %(end)s
			  AND (%(company)s IS NULL OR %(company)s = '' OR la.company = %(company)s)
			""",
			{"start": start, "end": end, "company": company},
		)
	return _currency_result(
		result[0][0] if result and result[0] else 0,
		_lease_contract_doctype(),
		_month_route_filters(_lease_contract_doctype(), "start_date"),
	)
