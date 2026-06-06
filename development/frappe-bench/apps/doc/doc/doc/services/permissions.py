import frappe


ROLE_ORDER = {
	"viewer": 1,
	"editor": 2,
	"publisher": 3,
	"manager": 4,
}


def get_project_role(project: str, user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return "manager"

	project_doc = frappe.get_doc("DOC0010", project)
	for row in project_doc.members or []:
		if row.user == user:
			return row.role
	return None


def has_project_role(project: str, user: str | None, required_role: str) -> bool:
	current_role = get_project_role(project, user)
	if not current_role:
		return False
	return ROLE_ORDER.get(current_role, 0) >= ROLE_ORDER[required_role]
