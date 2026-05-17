import frappe
from frappe import _
from frappe.model.document import Document

from doc.doc.services.slug import normalize_slug, validate_slug


class DOC0020(Document):
	def before_naming(self):
		self.set_defaults()
		self.validate_version_key()

	def validate(self):
		self.set_defaults()
		self.validate_version_key()
		self.validate_unique_version_key()

	def after_insert(self):
		self.ensure_default_version()

	def on_update(self):
		self.clear_other_default_versions()

	def set_defaults(self):
		if not self.status:
			self.status = "draft"
		if not self.creation_mode:
			self.creation_mode = "blank"

	def validate_version_key(self):
		self.version_key = validate_slug(normalize_slug(self.version_key or self.title), allow_dot=True)

	def validate_unique_version_key(self):
		filters = {"project": self.project, "version_key": self.version_key}
		if not self.is_new():
			filters["name"] = ["!=", self.name]
		existing = frappe.db.exists(
			"DOC0020",
			filters,
		)
		if existing:
			frappe.throw(_("同一项目下文档版本 {0} 已存在。").format(self.version_key))

	def ensure_default_version(self):
		has_default = frappe.db.exists(
			"DOC0020",
			{"project": self.project, "is_default": 1, "name": ["!=", self.name]},
		)
		if has_default:
			return

		self.is_default = 1
		frappe.db.set_value("DOC0020", self.name, "is_default", 1)
		frappe.db.set_value("DOC0010", self.project, "default_version", self.name)

	def clear_other_default_versions(self):
		if not self.is_default:
			return
		for row in frappe.get_all("DOC0020", filters={"project": self.project, "is_default": 1, "name": ["!=", self.name]}):
			frappe.db.set_value("DOC0020", row.name, "is_default", 0)
		frappe.db.set_value("DOC0010", self.project, "default_version", self.name)
