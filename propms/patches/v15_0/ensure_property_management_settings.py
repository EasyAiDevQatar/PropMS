# -*- coding: utf-8 -*-
"""Ensure Property Management Settings single record exists."""

from __future__ import unicode_literals

import frappe


def execute():
	if not frappe.db.exists("DocType", "Property Management Settings"):
		return

	doc = frappe.get_single("Property Management Settings")
	if getattr(doc, "__islocal", False) or not doc.name:
		doc.insert(ignore_permissions=True)
