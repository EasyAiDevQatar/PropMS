# -*- coding: utf-8 -*-
"""Allow amended Lease Agreements to share the same contract number."""

from __future__ import unicode_literals

import frappe


def execute():
    table = "tabLease Agreement"
    column = "contract_number"

    indexes = frappe.db.sql(
        """
        SHOW INDEX FROM `tabLease Agreement`
        WHERE Column_name = %s AND Non_unique = 0
        """,
        column,
        as_dict=True,
    )

    for index in indexes:
        if index.Key == "PRIMARY":
            continue
        frappe.db.sql_ddl(
            "ALTER TABLE `{table}` DROP INDEX `{key}`".format(
                table=table, key=index.Key
            )
        )

    frappe.clear_cache(doctype="Lease Agreement")
