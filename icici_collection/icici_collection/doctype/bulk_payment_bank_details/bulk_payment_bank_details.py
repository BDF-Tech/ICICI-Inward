# Copyright (c) 2024, Erpdata and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import io
from pandas import DataFrame, ExcelWriter
from openpyxl import Workbook
from datetime import datetime,date
from frappe import _

class BulkPaymentBankDetails(Document):
	def autoname(self):
		settings = frappe.get_doc('Bulk Payment Bank Details Settings')
		count = len(frappe.get_all("Bulk Payment Bank Details",filters = {'posting_date':['=',date.today()]})) + 1
		self.name = f"{settings.bank_code}_{datetime.now().day:02}{datetime.now().month:02}{datetime.now().year}_{count:03}"

	@frappe.whitelist()
	def get_data(self):
		filters={}
		if self.from_date and self.to_date:
			filters.update({"posting_date":["between",[self.from_date,self.to_date]]})
		if self.mode_of_payment:
			filters.update({"mode_of_payment":self.mode_of_payment})
		if self.party_type:
			filters.update({"party_type":self.party_type})
		filters.update({"docstatus":0})

		f =frappe.get_all('Payment Entry',filters,["*"])
		self.items=[]
		for d in f:
			bank_acc = frappe.get_doc("Bank Account", d.party_bank_account)
			company_account_no=frappe.db.get_value("Bank Account",d.bank_account,"bank_account_no")


			self.append("items",{
				"debit_ac_no":company_account_no,
				"beneficiary_ac_no":bank_acc.bank_account_no,
				"party_id":d.party,
				"party_name":d.party_name,
				"paid_amount":d.paid_amount,
				"posting_date":d.posting_date,
				"ifsc":bank_acc.branch_code,
				"remark":self.remark,
				"bank":bank_acc.bank
			})
   
	@frappe.whitelist()
	def generate_excel(self):
		data = {
			'Debit Ac No': [], 'Beneficiary Ac No': [],'ERP Code': [], 'Beneficiary Name': [], 'Amt': [], 'Pay Mod': [], 'Date': [], 'IFSC': [],
			 'Company Mail': [], 'Remarks': [], 'Payable Location': [], 'Print Location': [], 'Bene Mobile No.': [], 'Bene Email ID': [],
			'Bene add1': [], 'Bene add2': [], 'Bene add3': [], 'Bene add4': [], 'Add Details 1': [], 'Add Details 2': [], 'Add Details 3': [], 'Add Details 4': [], 'Add Details 5': []
		}
		month = ['Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sep', 'Oct', 'Nov', 'Dec']

		for item in self.get('items'):
			data['Debit Ac No'].append(item.debit_ac_no)
			data['Beneficiary Ac No'].append(item.beneficiary_ac_no)
			data['Beneficiary Name'].append(item.party_name)
			data['Amt'].append(item.paid_amount)
			if item.bank and item.bank == 'ICICI BANK':
				data['Pay Mod'].append('I')
			else:
				if item.paid_amount < 200000.00:
					data['Pay Mod'].append('N')
				else:
					data['Pay Mod'].append('R')
			if isinstance(item.posting_date, str):
				posting_date = datetime.strptime(item.posting_date, '%Y-%m-%d')
			else:
				posting_date = item.posting_date

			day = posting_date.day
			mth = posting_date.month
			year = posting_date.year
			mt = month[mth - 1]

			data['Date'].append(f'{day:02}-{mt}-{year}')
			data['IFSC'].append(item.ifsc)
			data['ERP Code'].append(item.party_id)
			data['Company Mail'].append('bastardairyfarm@gmail.com')
			data['Remarks'].append(self.remark)
			for key in ['Payable Location', 'Print Location', 'Bene Mobile No.', 'Bene Email ID',
						'Bene add1', 'Bene add2', 'Bene add3', 'Bene add4', 'Add Details 1',
						'Add Details 2', 'Add Details 3', 'Add Details 4', 'Add Details 5']:
				data[key].append('')
		
		df = DataFrame(data)
		output = io.BytesIO()
		with ExcelWriter(output, engine='openpyxl') as writer:
			df.to_excel(writer, index=False, sheet_name='Sheet1')
		output.seek(0)
		return output.getvalue()