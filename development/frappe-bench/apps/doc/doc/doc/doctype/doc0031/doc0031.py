import frappe
from frappe import _
from frappe.model.document import Document


class DOC0031(Document):
	def on_trash(self):
		frappe.throw(_("文档页面修订作为编辑历史，不能删除。"))
