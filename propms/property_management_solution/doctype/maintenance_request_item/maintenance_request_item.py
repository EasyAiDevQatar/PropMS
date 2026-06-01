# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
from frappe.utils import flt


class MaintenanceRequestItem(Document):
    def validate(self):
        self.amount = flt(self.qty or 1) * flt(self.rate or 0)
