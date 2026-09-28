import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabBulk Payment Bank Details` p
		SET p.total_paid_amount = (
			SELECT COALESCE(SUM(c.paid_amount), 0)
			FROM `tabBulk Payment Bank Details Item` c
			WHERE c.parent = p.name AND c.parenttype = 'Bulk Payment Bank Details'
		)
		"""
	)
