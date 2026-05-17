import re


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")


def normalize_slug(value: str) -> str:
	value = (value or "").strip().lower()
	value = re.sub(r"[^a-z0-9]+", "-", value)
	return value.strip("-")


def validate_slug(value: str, allow_dot: bool = False) -> str:
	value = (value or "").strip().lower()
	pattern = VERSION_KEY_PATTERN if allow_dot else SLUG_PATTERN
	if not value or not pattern.match(value):
		raise ValueError("slug 只允许小写字母、数字和分隔符。")
	return value
