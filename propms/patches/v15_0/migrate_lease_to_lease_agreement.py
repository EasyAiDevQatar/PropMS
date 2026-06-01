# -*- coding: utf-8 -*-
"""Migrate legacy `Lease` records into the new `Lease Agreement` doctype.

This is a one-shot best-effort migration:
  - Skips Lease records that already have a corresponding Lease Agreement
    (matched by name).
  - Creates a Lease Agreement with status='Active' / contract_type='Rent'.
  - Copies Lease Item rows into Lease Agreement Item rows.
  - Copies key Lease fields (property, customer, dates, security_deposit).
  - Leaves the original Lease intact so existing Sales Invoices that reference
    `Sales Invoice.lease` still work; reports already join on both.
"""

from __future__ import unicode_literals

import frappe


def execute():
    if not frappe.db.exists("DocType", "Lease") or not frappe.db.exists(
        "DocType", "Lease Agreement"
    ):
        return

    leases = frappe.db.sql(
        """
        SELECT name
        FROM `tabLease`
        WHERE COALESCE(lease_status, '') NOT IN ('Closed', 'Not Materialized')
        """,
        as_dict=True,
    )

    for row in leases:
        lease_name = row.name
        if frappe.db.exists("Lease Agreement", lease_name):
            continue

        try:
            _migrate_one(lease_name)
        except Exception:
            frappe.log_error(
                "Lease -> Lease Agreement migration failed",
                "Lease {0}".format(lease_name),
            )

    frappe.db.commit()


def _migrate_one(lease_name):
    lease = frappe.get_doc("Lease", lease_name)

    company = lease.company
    if not company and lease.property:
        company = frappe.db.get_value("Property", lease.property, "company")

    customer = lease.lease_customer or lease.customer
    if not customer:
        return

    unit = _resolve_unit_from_property(lease.property)

    agreement = frappe.new_doc("Lease Agreement")
    agreement.contract_number = lease_name
    agreement.customer = customer
    agreement.company = company
    agreement.contract_type = "Rent"
    agreement.status = _map_lease_status(lease.lease_status)
    agreement.property = lease.property
    if unit:
        agreement.unit = unit
    agreement.start_date = lease.start_date
    agreement.end_date = lease.end_date
    agreement.security_deposit = lease.security_deposit or 0
    agreement.payment_frequency = "Monthly"
    agreement.days_to_invoice_in_advance = lease.days_to_invoice_in_advance or 0

    for li in lease.lease_item or []:
        agreement.append(
            "items",
            {
                "item": li.lease_item,
                "qty": 1,
                "rate": li.amount,
                "frequency": _map_frequency(li.frequency),
                "tax_template": None,
            },
        )

    agreement.flags.ignore_permissions = True
    agreement.flags.ignore_validate = True
    agreement.flags.ignore_mandatory = True
    agreement.insert(ignore_permissions=True, ignore_mandatory=True)


def _resolve_unit_from_property(property_name):
    if not property_name:
        return None
    return frappe.db.get_value("Unit Master", {"property": property_name}, "name")


def _map_lease_status(legacy):
    mapping = {
        "Active": "Active",
        "Closed": "Cancelled",
        "Not Materialized": "Cancelled",
        "Renewal to Previous Lease": "Active",
        "Adendum to Previous Lease": "Active",
        "Vacating": "Active",
    }
    return mapping.get((legacy or "").strip(), "Active")


def _map_frequency(legacy):
    mapping = {
        "Monthly": "Monthly",
        "Bi-Monthly": "Monthly",
        "Quarterly": "Quarterly",
        "Annually": "Yearly",
        "6 months": "Half Yearly",
    }
    return mapping.get((legacy or "").strip(), "Monthly")
