import frappe
from frappe.tests import UnitTestCase


class TestDOC0020(UnitTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def create_project(self):
		return frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()

	def test_first_version_becomes_default(self):
		project = self.create_project()
		version = frappe.get_doc(
			{"doctype": "DOC0020", "project": project.name, "version_key": "V1", "title": "v1"}
		).insert()

		project.reload()
		self.assertEqual(version.version_key, "v1")
		self.assertEqual(version.is_default, 1)
		self.assertEqual(project.default_version, version.name)

	def test_rejects_duplicate_version_key_in_project(self):
		project = self.create_project()
		frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1 copy"}).insert()

	def test_only_one_default_version_per_project(self):
		project = self.create_project()
		first = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		second = frappe.get_doc(
			{"doctype": "DOC0020", "project": project.name, "version_key": "v2", "title": "v2", "is_default": 1}
		).insert()

		first.reload()
		self.assertEqual(first.is_default, 0)
		self.assertEqual(second.is_default, 1)
