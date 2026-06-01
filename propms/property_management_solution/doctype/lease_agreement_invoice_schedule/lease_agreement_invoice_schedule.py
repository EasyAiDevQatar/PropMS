# -*- coding: utf-8 -*-
# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
from frappe.utils import flt


class LeaseAgreementInvoiceSchedule(Document):
    def validate(self):
        self.total_amount = flt(self.amount) + flt(self.deposit_amount)
