# -*- coding: utf-8 -*-
"""Remove the Real Estate Invoice Request and Payment Schedule doctypes.

Both were prototypes that wrapped Sales Invoice / Payment Entry generation. We
now use the standard ERPNext Sales Invoice + Payment Entry directly, and the
schedule lives as a child table on Lease Agreement.
"""

from __future__ import unicode_literals

import frappe


REPLACED_DOCTYPES = (
    "Real Estate Invoice Request",
    "Payment Schedule",
)


def execute():
    for doctype in REPLACED_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            continue

        # Drop any existing rows of this doctype so they don't block deletion
        try:
            frappe.db.sql("DELETE FROM `tab{0}`".format(doctype.replace("`", "")))
        except Exception:
            pass

        try:
            frappe.delete_doc("DocType", doctype, force=True, ignore_missing=True)
        except Exception:
            frappe.db.delete("DocType", {"name": doctype})

    frappe.clear_cache()
