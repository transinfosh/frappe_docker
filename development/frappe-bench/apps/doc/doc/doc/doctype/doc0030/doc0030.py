import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from doc.doc.services.slug import normalize_slug, validate_slug


class DOC0030(Document):
	def validate(self):
		self.set_defaults()
		self.validate_slug()
		self.validate_parent()
		self.set_path()
		self.validate_unique_path()

	def after_insert(self):
		self.create_revision("manual_save")

	def on_update(self):
		if self.flags.in_insert:
			return
		if self.flags.skip_revision:
			return
		if self.has_value_changed("content_markdown") or self.has_value_changed("title") or self.has_value_changed("summary"):
			self.create_revision("manual_save")

	def set_defaults(self):
		if not self.status:
			self.status = "draft"
		if not self.review_status:
			self.review_status = "draft"
		if not self.doc_type:
			self.doc_type = "other"
		if self.sort_order is None:
			self.sort_order = 0

	def validate_slug(self):
		self.slug = validate_slug(normalize_slug(self.slug or self.title))

	def validate_parent(self):
		if not self.parent_page:
			return
		if self.parent_page == self.name:
			frappe.throw(_("父页面不能是当前页面。"))
		parent = frappe.get_doc("DOC0030", self.parent_page)
		if parent.project != self.project or parent.doc_version != self.doc_version:
			frappe.throw(_("父页面必须属于同一项目和文档版本。"))

	def set_path(self):
		if not self.parent_page:
			self.path = self.slug
			return
		parent_path = frappe.db.get_value("DOC0030", self.parent_page, "path")
		self.path = f"{parent_path}/{self.slug}"

	def validate_unique_path(self):
		existing = frappe.db.exists(
			"DOC0030",
			{"doc_version": self.doc_version, "path": self.path, "name": ["!=", self.name]},
		)
		if existing:
			frappe.throw(_("同一文档版本下路径 {0} 已存在。").format(self.path))

	def create_revision(self, change_type):
		next_revision_no = (frappe.db.count("DOC0031", {"page": self.name}) or 0) + 1
		revision = frappe.get_doc(
			{
				"doctype": "DOC0031",
				"page": self.name,
				"project": self.project,
				"doc_version": self.doc_version,
				"revision_no": next_revision_no,
				"title": self.title,
				"content_markdown": self.content_markdown,
				"summary": self.summary,
				"change_type": change_type,
				"created_by": frappe.session.user,
				"created_at": now_datetime(),
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("DOC0030", self.name, "latest_revision", revision.name, update_modified=False)
		self.latest_revision = revision.name


@frappe.whitelist()
def restore_revision(page: str, revision: str):
	page_doc = frappe.get_doc("DOC0030", page)
	revision_doc = frappe.get_doc("DOC0031", revision)
	if revision_doc.page != page_doc.name:
		frappe.throw(_("修订记录不属于当前页面。"))

	page_doc.title = revision_doc.title
	page_doc.content_markdown = revision_doc.content_markdown
	page_doc.summary = revision_doc.summary
	page_doc.flags.skip_revision = True
	page_doc.save()
	page_doc.create_revision("restore")
	return page_doc
