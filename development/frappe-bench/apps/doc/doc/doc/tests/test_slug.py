import unittest

from doc.doc.services.slug import normalize_slug, validate_slug


class TestSlugService(unittest.TestCase):
	def test_normalize_slug_lowercases_and_replaces_spaces(self):
		self.assertEqual(normalize_slug("Create Order API"), "create-order-api")

	def test_validate_slug_rejects_invalid_characters(self):
		with self.assertRaises(ValueError):
			validate_slug("Create_Order")

	def test_validate_slug_allows_version_key_dots(self):
		self.assertEqual(validate_slug("v1.1", allow_dot=True), "v1.1")
