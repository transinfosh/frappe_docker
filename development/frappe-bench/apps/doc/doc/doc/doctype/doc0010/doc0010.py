import frappe
from frappe import _
from frappe.model.document import Document

from doc.doc.services.slug import normalize_slug, validate_slug


class DOC0010(Document):
	def validate(self):
		self.set_defaults()
		self.validate_slug()
		self.validate_members()

	def set_defaults(self):
		if not self.status:
			self.status = "active"

	def validate_slug(self):
		self.slug = validate_slug(normalize_slug(self.slug or self.title))

	def validate_members(self):
		users = set()
		for row in self.members or []:
			if row.user in users:
				frappe.throw(_("同一项目中用户 {0} 只能出现一次。").format(row.user))
			users.add(row.user)
