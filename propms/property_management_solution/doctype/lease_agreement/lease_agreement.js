// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lease Agreement", {
	setup: function(frm) {
		frm.set_query("unit", function() {
			const filters = {};
			if (frm.doc.property) {
				filters.property = frm.doc.property;
			}

			return { filters };
		});
	},

	unit: function(frm) {
		if (!frm.doc.unit) {
			return;
		}

		frappe.db.get_value("Unit Master", frm.doc.unit, ["property", "rent_amount"], function(value) {
			if (value.property && !frm.doc.property) {
				frm.set_value("property", value.property);
			}
			if (value.rent_amount && !frm.doc.monthly_rent) {
				frm.set_value("monthly_rent", value.rent_amount);
			}
		});
	},
});
