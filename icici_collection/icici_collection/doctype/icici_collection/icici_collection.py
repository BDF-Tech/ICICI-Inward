import frappe
from frappe.model.document import Document
from frappe.utils import cstr
from base64 import b64decode,b64encode
from io import BytesIO
import qrcode
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import json
import os
from datetime import datetime


class ICICICollection(Document):
    def before_save(self):
        self.decrypt_api_data()
        
    def load_private_key(self,file_path):
        with open(file_path, 'rb') as private_file:
            private_key = RSA.import_key(private_file.read())
        return private_key
    
    def decrypt_api_data(self):
        encrypted_data_base64 = self.raw_encrypted_api_data
        encrypted_data = b64decode(encrypted_data_base64)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = frappe.db.get_single_value("Bulk Payment Bank Details Settings","file_name")
        private_key_path = os.path.join(current_dir, file_name)
        # private_key_path = os.path.join(current_dir, 'private-key.pem')
        
        private_key = self.load_private_key(private_key_path)
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_data = cipher.decrypt(encrypted_data, None)
        decrypted_data = json.loads(decrypted_data)
        
        self.sub_merchant_id = decrypted_data['subMerchantId']
        self.payer_mobile = decrypted_data['PayerMobile']
        self.txn_completion_date = decrypted_data['TxnCompletionDate']
        self.terminal_id = decrypted_data['terminalId']
        self.payer_name = decrypted_data['PayerName']
        self.payer_amount = decrypted_data['PayerAmount']
        self.payer_va = decrypted_data['PayerVA']
        self.bank_rrn = decrypted_data['BankRRN']
        self.merchant_id = decrypted_data['merchantId']
        self.payer_acc_type = decrypted_data['PayerAccountType']
        self.txn_init_date = decrypted_data['TxnInitDate']
        self.txn_status = decrypted_data['TxnStatus']
        self.merchant_tran_id = decrypted_data['merchantTranId']
    
    
       
       
        
#call to generate QR Code.
@frappe.whitelist()
def generate_qr(name):
    url = frappe.db.get_single_value("Bulk Payment Bank Details Settings","url")
    qr_str = url.format(name=name)
    return get_qr_code(qr_str)


def get_qr_code(data: str) -> str:
    qr_code_bytes = get_qr_code_bytes(data, format="PNG")
    base_64_string = bytes_to_base64_string(qr_code_bytes)

    return add_file_info(base_64_string)


def add_file_info(data: str) -> str:
    """Add info about the file type and encoding.
    
    This is required so the browser can make sense of the data."""
    return f"data:image/png;base64, {data}"

def get_qr_code_bytes(data, format: str) -> bytes:
    """Create a QR code and return the bytes."""
    img = qrcode.make(data)

    buffered = BytesIO()
    img.save(buffered, format=format)

    return buffered.getvalue()
def bytes_to_base64_string(data: bytes) -> str:
    """Convert bytes to a base64 encoded string."""
    return b64encode(data).decode("utf-8")



def gen_response(status, message, data=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(str(message)).get_text()
    else:
        frappe.response["message"] = message
    frappe.response["data"] = data


def exception_handel(e):
    frappe.log_error(title="Mobile App Error", message=frappe.get_traceback())
    if hasattr(e, "http_status_code"):
        return gen_response(e.http_status_code, cstr(e))
    else:
        return gen_response(500, cstr(e))




@frappe.whitelist()
def set_api_data():
    try:
        # Read raw data from the request body
        raw_data = frappe.local.request.get_data(as_text=True)
        frappe.logger().debug(f"Received raw data: {raw_data}")

        # Insert the raw text into the 'raw_encrypted_api_data' field
        doc = frappe.get_doc({
            "doctype": "ICICI Collection",
            "raw_encrypted_api_data": raw_data
        }).insert()

        frappe.logger().debug(f"Document created: {doc.name}")

        gen_response(200, "Data Received Successfully.", doc)
    except frappe.AuthenticationError:
        gen_response(500, frappe.response["message"])
    except Exception as e:
        frappe.logger().error(f"Error occurred: {str(e)}")
        return exception_handel(e)


        


