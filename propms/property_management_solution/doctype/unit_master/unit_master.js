// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Unit Master", {
	setup: function(frm) {
		frm.set_query("income_account", function() {
			return {
				filters: {
					root_type: "Income",
					is_group: 0,
				},
			};
		});

		frm.set_query("cost_center", function() {
			return {
				filters: {
					is_group: 0,
				},
			};
		});
	},
});
