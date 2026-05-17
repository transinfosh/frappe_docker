import frappe


MERMAID_DIAGRAM_TYPES = (
	"flowchart",
	"graph",
	"sequenceDiagram",
	"classDiagram",
	"stateDiagram",
	"erDiagram",
	"gantt",
	"journey",
	"pie",
	"mindmap",
	"timeline",
	"gitGraph",
	"quadrantChart",
)


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
	doc.content_markdown = normalize_mermaid_markdown(content_markdown or "")
	doc.save()
	return get_page_detail(doc.name)


def normalize_mermaid_markdown(markdown: str) -> str:
	lines = markdown.split("\n")
	normalized_lines = []
	in_mermaid_block = False

	for line in lines:
		stripped = line.strip()
		if stripped.startswith("```"):
			language = stripped[3:].strip().split(" ", 1)[0]
			if not in_mermaid_block and language == "mermaid":
				in_mermaid_block = True
			elif in_mermaid_block:
				in_mermaid_block = False
			normalized_lines.append(line)
			continue

		if in_mermaid_block:
			normalized_lines.append(decode_mermaid_entities(line))
		else:
			normalized_lines.append(line)

	return normalize_indented_mermaid_blocks("\n".join(normalized_lines))


def normalize_indented_mermaid_blocks(markdown: str) -> str:
	lines = markdown.split("\n")
	normalized_lines = []
	index = 0

	while index < len(lines):
		line = lines[index]
		if not line.startswith(("    ", "\t")):
			normalized_lines.append(line)
			index += 1
			continue

		block_lines = []
		while index < len(lines) and (lines[index].startswith(("    ", "\t")) or lines[index] == ""):
			block_lines.append(lines[index][4:] if lines[index].startswith("    ") else lines[index].lstrip("\t"))
			index += 1

		content = decode_mermaid_entities("\n".join(block_lines).rstrip())
		if is_mermaid_content(content):
			normalized_lines.extend(["```mermaid", content, "```"])
		else:
			normalized_lines.extend([f"    {block_line}" if block_line else "" for block_line in block_lines])

	return "\n".join(normalized_lines)


def is_mermaid_content(content: str) -> bool:
	first_line = next((line.strip() for line in content.split("\n") if line.strip()), "")
	return first_line.startswith(MERMAID_DIAGRAM_TYPES)


def decode_mermaid_entities(content: str) -> str:
	return (
		content.replace("&gt;", ">")
		.replace("&lt;", "<")
		.replace("&amp;", "&")
		.replace("&quot;", '"')
		.replace("&#39;", "'")
	)
