// Copyright (c) 2026, Aakvatech and contributors

frappe.ui.form.on("Property Viewing", {
	setup(frm) {
		frm.set_query("unit", () => {
			const filters = {};
			if (frm.doc.property) filters.property = frm.doc.property;
			return { filters };
		});
	},
});
