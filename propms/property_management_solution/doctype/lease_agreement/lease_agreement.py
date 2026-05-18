# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class LeaseAgreement(Document):
    def validate(self):
        self.validate_dates()
        self.set_property_from_unit()

    def validate_dates(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw(_("End Date cannot be before Start Date"))

    def set_property_from_unit(self):
        if not self.unit:
            return

        unit_property = frappe.db.get_value("Unit Master", self.unit, "property")
        if unit_property and not self.property:
            self.property = unit_property

        if unit_property and self.property and self.property != unit_property:
            frappe.throw(_("Selected Unit does not belong to the selected Property"))
