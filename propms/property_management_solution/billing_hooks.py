# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors

from __future__ import unicode_literals

import frappe
from frappe.utils import flt


def sync_lease_links_on_payment_entry(doc, method=None):
	"""Copy lease/property/unit from referenced Sales Invoice onto Payment Entry."""
	if doc.get("propms_lease_agreement"):
		return

	lease_links = _resolve_lease_links_from_payment(doc)
	if not lease_links:
		return

	doc.propms_lease_agreement = lease_links["lease_agreement"]
	doc.propms_property = lease_links.get("property")
	doc.propms_unit = lease_links.get("unit")


def update_lease_on_payment_entry_submit(doc, method=None):
	"""After payment is submitted, link it on the lease invoice schedule."""
	if doc.docstatus != 1:
		return

	lease_links = _resolve_lease_links_from_payment(doc)
	if not lease_links:
		return

	if not doc.get("propms_lease_agreement"):
		frappe.db.set_value(
			"Payment Entry",
			doc.name,
			{
				"propms_lease_agreement": lease_links["lease_agreement"],
				"propms_property": lease_links.get("property"),
				"propms_unit": lease_links.get("unit"),
			},
			update_modified=False,
		)

	for ref in doc.get("references") or []:
		if ref.reference_doctype != "Sales Invoice" or not ref.reference_name:
			continue
		_update_schedule_for_invoice(
			lease_links["lease_agreement"],
			ref.reference_name,
			doc.name,
		)

	_refresh_lease_payment_count(lease_links["lease_agreement"])


def update_lease_on_payment_entry_cancel(doc, method=None):
	"""Revert invoice schedule payment link when a payment is cancelled."""
	lease = doc.get("propms_lease_agreement")
	if not lease:
		lease_links = _resolve_lease_links_from_payment(doc)
		lease = lease_links.get("lease_agreement") if lease_links else None
	if not lease:
		return

	for ref in doc.get("references") or []:
		if ref.reference_doctype != "Sales Invoice" or not ref.reference_name:
			continue

		schedule_row = frappe.db.get_value(
			"Lease Agreement Invoice Schedule",
			{"parent": lease, "sales_invoice": ref.reference_name},
			["name", "payment_entry"],
			as_dict=True,
		)
		if not schedule_row or schedule_row.payment_entry != doc.name:
			continue

		latest_pe = _get_latest_payment_entry_for_invoice(ref.reference_name, lease)
		si = frappe.db.get_value(
			"Sales Invoice",
			ref.reference_name,
			["status", "outstanding_amount"],
			as_dict=True,
		)
		is_paid = si and flt(si.outstanding_amount) <= 0 and si.status == "Paid"

		frappe.db.set_value(
			"Lease Agreement Invoice Schedule",
			schedule_row.name,
			{
				"payment_entry": latest_pe,
				"status": "Paid" if is_paid and latest_pe else "Invoiced",
			},
			update_modified=False,
		)

	_refresh_lease_payment_count(lease)


def set_lease_links_on_sales_invoice(invoice, lease):
	"""Stamp lease agreement links on a Sales Invoice document."""
	invoice.propms_lease_agreement = lease.name
	invoice.propms_property = lease.property
	invoice.propms_unit = lease.unit


def set_lease_links_on_payment_entry(payment_entry, lease):
	"""Stamp lease agreement links on a Payment Entry document."""
	payment_entry.propms_lease_agreement = lease.name
	payment_entry.propms_property = lease.property
	payment_entry.propms_unit = lease.unit


def _resolve_lease_links_from_payment(doc):
	for ref in doc.get("references") or []:
		if ref.reference_doctype != "Sales Invoice" or not ref.reference_name:
			continue

		si = frappe.db.get_value(
			"Sales Invoice",
			ref.reference_name,
			["propms_lease_agreement", "propms_property", "propms_unit"],
			as_dict=True,
		)
		if si and si.propms_lease_agreement:
			return {
				"lease_agreement": si.propms_lease_agreement,
				"property": si.propms_property,
				"unit": si.propms_unit,
			}

		schedule = frappe.db.get_value(
			"Lease Agreement Invoice Schedule",
			{"sales_invoice": ref.reference_name},
			["parent", "parent as lease_agreement"],
			as_dict=True,
		)
		if not schedule:
			continue

		lease = frappe.get_doc("Lease Agreement", schedule.lease_agreement)
		return {
			"lease_agreement": lease.name,
			"property": lease.property,
			"unit": lease.unit,
		}

	return None


def _update_schedule_for_invoice(lease, sales_invoice, payment_entry):
	schedule_row = frappe.db.get_value(
		"Lease Agreement Invoice Schedule",
		{"parent": lease, "sales_invoice": sales_invoice},
		"name",
	)
	if not schedule_row:
		return

	updates = {"payment_entry": payment_entry}
	si = frappe.db.get_value(
		"Sales Invoice",
		sales_invoice,
		["status", "outstanding_amount"],
		as_dict=True,
	)
	if si and flt(si.outstanding_amount) <= 0 and si.status == "Paid":
		updates["status"] = "Paid"

	frappe.db.set_value(
		"Lease Agreement Invoice Schedule",
		schedule_row,
		updates,
		update_modified=False,
	)


def _get_latest_payment_entry_for_invoice(sales_invoice, lease):
	result = frappe.db.sql(
		"""
		SELECT pe.name
		FROM `tabPayment Entry` pe
		INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
		WHERE pe.docstatus = 1
		  AND per.reference_doctype = 'Sales Invoice'
		  AND per.reference_name = %(sales_invoice)s
		  AND (
			pe.propms_lease_agreement = %(lease)s
			OR pe.propms_lease_agreement IS NULL
			OR pe.propms_lease_agreement = ''
		  )
		ORDER BY pe.posting_date DESC, pe.creation DESC
		LIMIT 1
		""",
		{"sales_invoice": sales_invoice, "lease": lease},
	)
	return result[0][0] if result else None


def _refresh_lease_payment_count(lease):
	from propms.property_management_solution.doctype.lease_agreement.lease_agreement import (
		get_linked_payment_count,
	)

	frappe.db.set_value(
		"Lease Agreement",
		lease,
		"linked_payment_count",
		get_linked_payment_count(lease),
		update_modified=False,
	)
