import frappe
from frappe.tests import UnitTestCase


class TestDOC0010(UnitTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_project_defaults_and_slug_normalization(self):
		project = frappe.get_doc(
			{
				"doctype": "DOC0010",
				"title": "支付系统",
				"slug": "Payment System",
			}
		).insert()

		self.assertEqual(project.slug, "payment-system")
		self.assertEqual(project.status, "active")
		self.assertEqual(project.is_public, 0)

	def test_rejects_duplicate_project_slug(self):
		frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": "payment"}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "DOC0010", "title": "支付系统副本", "slug": "payment"}).insert()

	def test_rejects_duplicate_member_user(self):
		project = frappe.get_doc(
			{
				"doctype": "DOC0010",
				"title": "支付系统",
				"slug": "payment-members",
				"members": [
					{"user": "Administrator", "role": "manager"},
					{"user": "Administrator", "role": "editor"},
				],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			project.insert()
