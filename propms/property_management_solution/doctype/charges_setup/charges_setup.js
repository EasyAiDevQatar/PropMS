// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Charges Setup", {
	setup: function(frm) {
		frm.set_query("income_account", function() {
			return {
				filters: {
					root_type: "Income",
					is_group: 0,
				},
			};
		});
	},
});
