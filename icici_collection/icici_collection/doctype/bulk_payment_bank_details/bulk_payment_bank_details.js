// Copyright (c) 2024, Erpdata and contributors
// For license information, please see license.txt
// hello
frappe.ui.form.on('Bulk Payment Bank Details', {
	get_records: function(frm) {
		frm.call({
			method:'get_data',
			doc: frm.doc,
		})
	 },
	refresh:function(frm){
	frm.set_query("party_type", function() {
		return {
			filters: {
				"name": ["in", ["Supplier", "Employee","Customer"]]
			}
		}
	})
	}
});

function download(file, blob) {
    var element = document.createElement('a');
    var url = URL.createObjectURL(blob);
    element.href = url;
    element.download = file;
    document.body.appendChild(element);
    element.click();
    setTimeout(function() {
        document.body.removeChild(element);
        window.URL.revokeObjectURL(url);
    }, 0);
}

frappe.ui.form.on('Bulk Payment Bank Details', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Download Excel'), function() {
                frappe.call({
                    method: 'generate_excel',
                    doc: frm.doc,
                    callback: function(response) {
                        if (response.message) {
                            var byteArray = new Uint8Array(response.message);
                            var blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                            var filename = `${frm.doc.name}.xlsx`;
                            download(filename, blob);
                        } else {
                            frappe.msgprint('Excel download failed.');
                        }
                    }
                });
            });
        }
    }
});