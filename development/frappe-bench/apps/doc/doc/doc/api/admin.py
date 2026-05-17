import frappe


@frappe.whitelist()
def get_project_spaces() -> list[dict]:
	projects = frappe.get_all(
		"DOC0010",
		fields=["name", "title", "slug", "description", "is_public", "default_version", "status"],
		order_by="title asc",
	)
	return projects


@frappe.whitelist()
def get_versions(project: str) -> list[dict]:
	return frappe.get_all(
		"DOC0020",
		filters={"project": project},
		fields=["name", "title", "version_key", "status", "is_default"],
		order_by="is_default desc, creation asc",
	)


@frappe.whitelist()
def get_page_tree(doc_version: str) -> list[dict]:
	pages = frappe.get_all(
		"DOC0030",
		filters={"doc_version": doc_version},
		fields=["name", "title", "slug", "path", "parent_page", "sort_order", "status", "doc_type"],
		order_by="sort_order asc, title asc",
	)
	by_name = {}
	roots = []

	for page in pages:
		page["children"] = []
		by_name[page["name"]] = page

	for page in pages:
		parent_page = page.get("parent_page")
		if parent_page and parent_page in by_name:
			by_name[parent_page]["children"].append(page)
		else:
			roots.append(page)

	return roots


@frappe.whitelist()
def get_page_detail(page: str) -> dict:
	doc = frappe.get_doc("DOC0030", page)
	return {
		"name": doc.name,
		"title": doc.title,
		"slug": doc.slug,
		"path": doc.path,
		"project": doc.project,
		"doc_version": doc.doc_version,
		"parent_page": doc.parent_page,
		"content_markdown": doc.content_markdown or "",
		"summary": doc.summary or "",
		"status": doc.status,
		"review_status": doc.review_status,
		"doc_type": doc.doc_type,
		"latest_revision": doc.latest_revision,
	}


@frappe.whitelist()
def save_page_content(page: str, content_markdown: str) -> dict:
	doc = frappe.get_doc("DOC0030", page)
	doc.content_markdown = content_markdown or ""
	doc.save()
	return get_page_detail(doc.name)
