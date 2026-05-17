# Docs Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建独立 `docs` Frappe 应用，并完成企业文档平台第一可交付切片：三文档先行、核心 DocType、项目级权限、文档版本、页面修订和基础后端测试。

**Architecture:** 第一阶段只实现平台内核，不实现 Vue 编辑端和外部阅读端。Frappe DocType 承载 `DOC0010` 到 `DOC0031` 的项目、成员、版本、页面和修订模型；后端 Python 负责 slug/path、版本复制、修订记录和项目级权限兜底；测试先覆盖模型规则和可发布前置能力。

**Tech Stack:** Frappe Framework、DocType JSON、Python `Document`、Frappe 白名单接口、`frappe.tests.IntegrationTestCase`、bench 隔离测试站点、中文业务文档。

---

## Scope Boundary

本计划只覆盖设计文档中的“平台骨架”切片：

- 创建 `docs` app。
- 完成三文档先行：业务规格说明、BDD 场景、测试说明。
- 建立核心 DocType：`DOC0010`、`DOC0011`、`DOC0020`、`DOC0030`、`DOC0031`。
- 实现项目、版本、页面、页面修订的基础后端规则。
- 实现项目成员角色判断的服务函数。
- 用隔离测试站点验证核心模型。

本计划不覆盖：

- `DOC0040` 图表块。
- `DOC0050` / `DOC0051` 发布快照。
- `DOC0060` 分享链接。
- `DOC0070` 搜索索引。
- `DOC0080` 发布记录。
- Vue SPA、Milkdown、Mermaid、draw.io。

这些能力应在后续计划中按“发布治理”“图表与分享”“编辑阅读闭环”继续拆分。

## File Structure

`docs` 作为 app 名会生成 Python 包 `frappe-bench/apps/docs/docs`。由于应用根目录下的常规 `docs/` 文档目录会与包目录同名冲突，本计划将三文档先行产物放在应用根目录的 `design_docs/docs/` 下。代码仍使用 Frappe 标准包路径。

- Create: `frappe-bench/apps/docs/`
  - 独立 Frappe 应用根目录，由 `bench new-app docs --no-git` 生成。
- Modify: `frappe-bench/apps/docs/docs/hooks.py`
  - 设置应用中文标题、app home 和基础配置。
- Modify: `frappe-bench/apps/docs/docs/modules.txt`
  - 确认模块名为 `Docs`。
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-业务规格说明.md`
  - 第一切片业务规格说明。
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-BDD场景.md`
  - 第一切片 BDD 场景。
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-测试说明.md`
  - 第一切片测试说明。
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0010/`
  - `DOC0010 文档项目` DocType JSON、Python、测试。
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0011/`
  - `DOC0011 文档项目成员` 子表 DocType JSON、Python。
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0020/`
  - `DOC0020 文档版本` DocType JSON、Python、测试。
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/`
  - `DOC0030 文档页面` DocType JSON、Python、测试。
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0031/`
  - `DOC0031 文档页面修订` DocType JSON、Python。
- Create: `frappe-bench/apps/docs/docs/docs/services/permissions.py`
  - 项目级角色判断和权限兜底函数。
- Create: `frappe-bench/apps/docs/docs/docs/services/slug.py`
  - slug/path 规范化与生成辅助函数。
- Create: `frappe-bench/apps/docs/docs/docs/services/versioning.py`
  - 文档版本复制服务。

## Task 1: 创建 `docs` App 骨架

**Files:**
- Create: `frappe-bench/apps/docs/`
- Modify: `frappe-bench/apps/docs/docs/hooks.py`
- Modify: `frappe-bench/apps/docs/docs/modules.txt`

- [ ] **Step 1: 运行 app 创建命令**

Run from `/workspace/development/frappe-bench`:

```bash
bench new-app docs --no-git
```

When prompted, enter:

```text
App Title: 文档
App Publisher: Transinfo
App Description: Enterprise documentation platform
App Email: adam.wu@trinfo.net
App License: mit
```

Expected:

```text
App docs created
```

- [ ] **Step 2: 确认模块文件**

Open `frappe-bench/apps/docs/docs/modules.txt` and ensure it contains exactly:

```text
Docs
```

- [ ] **Step 3: 调整 hooks 基础信息**

Modify `frappe-bench/apps/docs/docs/hooks.py` so the top app metadata is:

```python
app_name = "docs"
app_title = "文档"
app_publisher = "Transinfo"
app_description = "Enterprise documentation platform"
app_email = "adam.wu@trinfo.net"
app_license = "mit"
app_home = "/docs-admin"
```

If `app_home` is not present in the generated file, add it after `app_license`.

- [ ] **Step 4: 运行基础导入检查**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost list-apps
```

Expected: command may fail if `test.localhost` does not exist. If it fails with missing site, proceed to Task 10 where the isolated site is created.

- [ ] **Step 5: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs
git commit -m "feat: create docs app skeleton"
```

## Task 2: 补齐三文档先行

**Files:**
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-业务规格说明.md`
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-BDD场景.md`
- Create: `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-测试说明.md`

- [ ] **Step 1: 创建文档目录**

```bash
mkdir -p /workspace/development/frappe-bench/apps/docs/design_docs/docs
```

- [ ] **Step 2: 创建业务规格说明**

Create `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-业务规格说明.md` with this content:

```markdown
# DOC0000 文档平台骨架业务规格说明

> 来源：`/workspace/development/docs/superpowers/specs/2026-05-17-docs-platform-design.md`
> 范围：`DOC0010` 文档项目、`DOC0011` 文档项目成员、`DOC0020` 文档版本、`DOC0030` 文档页面、`DOC0031` 文档页面修订。

## 1. 业务目标

文档平台骨架用于建立企业文档平台的基础数据模型。内部用户可以维护文档项目、项目成员、文档版本、树状页面和页面修订历史，为后续发布快照、阅读端、编辑端、图表和分享链接提供稳定基础。

## 2. 适用范围

本规格覆盖第一阶段平台内核，不覆盖 Vue 编辑端、外部阅读端、发布快照、图表块、分享链接和全文搜索。

## 3. 数据模型

### 3.1 DOC0010 文档项目

`DOC0010` 表示一个文档项目空间。关键字段：

| 字段 | 规则 |
| --- | --- |
| `title` | 必填，项目标题。 |
| `slug` | 必填，全局唯一，只允许小写字母、数字和连字符。 |
| `description` | 可选，项目说明。 |
| `is_public` | 默认 0，后续阅读端用于公开访问判断。 |
| `default_version` | 可选，指向默认 `DOC0020`。 |
| `status` | 必填，取值 `active`、`archived`，默认 `active`。 |
| `members` | 子表，关联 `DOC0011`。 |

### 3.2 DOC0011 文档项目成员

`DOC0011` 表示项目级内部权限成员。关键字段：

| 字段 | 规则 |
| --- | --- |
| `user` | 必填，Frappe 用户。 |
| `role` | 必填，取值 `viewer`、`editor`、`publisher`、`manager`。 |

同一个项目中同一个用户只能出现一次。

### 3.3 DOC0020 文档版本

`DOC0020` 表示项目下的产品文档版本空间，例如 `v1`、`v2`。关键字段：

| 字段 | 规则 |
| --- | --- |
| `project` | 必填，所属 `DOC0010`。 |
| `version_key` | 必填，同项目内唯一，只允许小写字母、数字、点号和连字符，推荐 `v1`、`v2`。 |
| `title` | 必填，版本标题。 |
| `is_default` | 默认 0；同一项目只能有一个默认版本。 |
| `status` | 必填，取值 `draft`、`published`、`archived`，默认 `draft`。 |
| `source_version` | 可选，从已有版本复制时记录来源版本。 |
| `creation_mode` | 必填，取值 `blank`、`copy`，默认 `blank`。 |

### 3.4 DOC0030 文档页面

`DOC0030` 表示文档版本空间内的草稿页面。关键字段：

| 字段 | 规则 |
| --- | --- |
| `project` | 必填，所属项目。 |
| `doc_version` | 必填，所属文档版本。 |
| `parent_page` | 可选，父页面必须属于同一项目和版本。 |
| `title` | 必填，页面标题。 |
| `slug` | 必填，同一父级下唯一，只允许小写字母、数字和连字符。 |
| `path` | 系统生成，同一版本内唯一。 |
| `doc_type` | 必填，取值 `api`、`manual`、`sdk`、`webhook`、`faq`、`error_code`、`architecture`、`changelog`、`other`，默认 `other`。 |
| `content_markdown` | Markdown 草稿内容。 |
| `summary` | 页面摘要。 |
| `sort_order` | 同级排序，默认 0。 |
| `status` | 必填，取值 `draft`、`published`、`archived`，默认 `draft`。 |
| `review_status` | 预留审批状态，默认 `draft`。 |
| `latest_revision` | 最近一次页面修订。 |

页面保存时系统根据父级路径生成 `path`。根页面 path 等于自身 slug，子页面 path 为 `{parent.path}/{slug}`。

### 3.5 DOC0031 文档页面修订

`DOC0031` 表示页面草稿编辑历史。关键字段：

| 字段 | 规则 |
| --- | --- |
| `page` | 必填，所属页面。 |
| `project` | 必填，冗余所属项目。 |
| `doc_version` | 必填，冗余所属版本。 |
| `revision_no` | 页面内递增，从 1 开始。 |
| `title` | 修订时页面标题。 |
| `content_markdown` | 修订时 Markdown 内容。 |
| `summary` | 修订说明或自动摘要。 |
| `change_type` | 取值 `manual_save`、`auto_save`、`restore`、`publish`，默认 `manual_save`。 |
| `created_by` | 修改人。 |
| `created_at` | 修改时间。 |

用户显式保存页面时创建修订记录。自动保存只更新当前草稿，不强制创建修订记录。

## 4. 业务规则

- `slug`、`version_key` 保存前必须规范化为小写。
- 项目 slug 全局唯一。
- 版本 key 在同一项目内唯一。
- 页面 path 在同一文档版本内唯一。
- 父页面必须属于同一项目和文档版本。
- 不能把页面设置为自身或后代页面的父级。
- 同一项目只能有一个默认文档版本。
- 创建第一个版本时，如果未指定默认版本，应自动设为默认版本。
- 页面显式保存时创建 `DOC0031` 修订记录，并更新 `DOC0030.latest_revision`。
- 恢复草稿时基于指定 `DOC0031` 覆盖页面草稿内容，并创建新的 `restore` 修订。
- `DOC0031` 为审计历史，不允许删除。

## 5. 非目标

- 本阶段不发布外部可读快照。
- 本阶段不实现图表块。
- 本阶段不实现私密分享链接。
- 本阶段不实现搜索索引。
- 本阶段不实现 Vue 编辑端或阅读端。

## 6. 风险与假设

- 应用名 `docs` 与常规文档目录名冲突，因此业务文档放在 `design_docs/docs/` 下。
- 第一阶段角色判断通过服务函数完成，Frappe 权限矩阵只提供基础保护。
- 页面移动后需要递归更新后代 path；第一阶段可以先实现保存当前页面和直接后代更新，复杂批量移动留给编辑端计划细化。
```

- [ ] **Step 3: 创建 BDD 场景**

Create `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-BDD场景.md` with this content:

```markdown
# DOC0000 文档平台骨架 BDD 场景

## Feature: 文档项目

### Scenario: 创建文档项目

```gherkin
Given 内部用户具备文档管理权限
When 用户创建标题为“支付系统”且 slug 为“payment”的 DOC0010
Then 系统应保存文档项目
And status 应为 active
And is_public 应为 0
```

### Scenario: 拒绝重复项目 slug

```gherkin
Given 已存在 slug 为 payment 的 DOC0010
When 用户再次创建 slug 为 payment 的 DOC0010
Then 系统应阻止保存
And 提示项目 slug 已存在
```

## Feature: 文档版本

### Scenario: 创建默认版本

```gherkin
Given 项目 payment 尚无默认版本
When 用户创建 version_key 为 v1 的 DOC0020
Then DOC0020.is_default 应为 1
And DOC0010.default_version 应指向该版本
```

### Scenario: 同一项目下版本 key 唯一

```gherkin
Given 项目 payment 已存在 version_key 为 v1 的 DOC0020
When 用户在 payment 下再次创建 version_key 为 v1 的 DOC0020
Then 系统应阻止保存
```

## Feature: 文档页面

### Scenario: 创建根页面

```gherkin
Given 项目 payment 存在 v1 文档版本
When 用户创建标题为“快速开始”且 slug 为 quick-start 的 DOC0030
Then 页面 path 应为 quick-start
And 页面 status 应为 draft
```

### Scenario: 创建子页面

```gherkin
Given 项目 payment 的 v1 下存在 path 为 api 的父页面
When 用户在 api 下创建 slug 为 create-order 的子页面
Then 子页面 path 应为 api/create-order
```

### Scenario: 父页面必须属于同一版本

```gherkin
Given 项目 payment 存在 v1 和 v2 两个版本
And v1 下存在 path 为 api 的页面
When 用户在 v2 页面中选择 v1 的 api 页面作为父页面
Then 系统应阻止保存
```

## Feature: 页面修订

### Scenario: 显式保存页面时创建修订

```gherkin
Given 项目 payment 的 v1 下存在页面 create-order
When 用户修改 Markdown 内容并保存
Then 系统应创建一条 DOC0031
And revision_no 应为该页面内的下一个序号
And DOC0030.latest_revision 应指向该修订
```

### Scenario: 基于历史修订恢复草稿

```gherkin
Given 页面 create-order 存在 revision_no 为 1 和 2 的修订
When 用户选择恢复 revision_no 为 1 的内容
Then DOC0030.content_markdown 应等于 revision_no 1 的内容
And 系统应创建一条 change_type 为 restore 的新修订
```
```

- [ ] **Step 4: 创建测试说明**

Create `frappe-bench/apps/docs/design_docs/docs/DOC0000-文档平台骨架-测试说明.md` with this content:

```markdown
# DOC0000 文档平台骨架测试说明

## 1. 测试范围

覆盖 `DOC0010`、`DOC0011`、`DOC0020`、`DOC0030`、`DOC0031` 的后端模型规则、权限辅助函数、版本复制服务和页面修订服务。

## 2. 前置数据

- Frappe 隔离测试站点：`test.localhost`。
- 已安装 app：`docs`。
- 管理员账号：`Administrator` / `admin`。

## 3. 用例映射表

| 编号 | 场景组 | 覆盖点 | 对应 BDD | 测试层级 | 优先级 |
| --- | --- | --- | --- | --- | --- |
| T-DOC0000-001 | 项目 | 创建项目默认值 | 创建文档项目 | 后端 | P0 |
| T-DOC0000-002 | 项目 | 项目 slug 全局唯一 | 拒绝重复项目 slug | 后端 | P0 |
| T-DOC0000-003 | 版本 | 首个版本自动成为默认版本 | 创建默认版本 | 后端 | P0 |
| T-DOC0000-004 | 版本 | 同项目版本 key 唯一 | 同一项目下版本 key 唯一 | 后端 | P0 |
| T-DOC0000-005 | 页面 | 根页面 path 生成 | 创建根页面 | 后端 | P0 |
| T-DOC0000-006 | 页面 | 子页面 path 生成 | 创建子页面 | 后端 | P0 |
| T-DOC0000-007 | 页面 | 父页面同版本校验 | 父页面必须属于同一版本 | 后端 | P0 |
| T-DOC0000-008 | 修订 | 保存页面创建修订 | 显式保存页面时创建修订 | 后端 | P0 |
| T-DOC0000-009 | 修订 | 基于历史修订恢复草稿 | 基于历史修订恢复草稿 | 接口 | P1 |

## 4. 自动化测试命令

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs
```

## 5. 手工验证

第一阶段无强制手工验证项。Desk 中可额外确认 DocType 字段展示和基础创建流程。

## 6. 回归范围

`docs` 是新 app，不应修改 `base`、`srm`、`quality` 等已有 app。
```

- [ ] **Step 5: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/design_docs/docs
git commit -m "docs: add platform foundation specs"
```

## Task 3: 添加基础服务函数测试

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/services/__init__.py`
- Create: `frappe-bench/apps/docs/docs/docs/services/slug.py`
- Create: `frappe-bench/apps/docs/docs/docs/tests/test_slug.py`

- [ ] **Step 1: 写 slug 服务失败测试**

Create `frappe-bench/apps/docs/docs/docs/tests/test_slug.py`:

```python
import unittest

from docs.docs.services.slug import normalize_slug, validate_slug


class TestSlugService(unittest.TestCase):
	def test_normalize_slug_lowercases_and_replaces_spaces(self):
		self.assertEqual(normalize_slug("Create Order API"), "create-order-api")

	def test_validate_slug_rejects_invalid_characters(self):
		with self.assertRaises(ValueError):
			validate_slug("Create_Order")

	def test_validate_slug_allows_version_key_dots(self):
		self.assertEqual(validate_slug("v1.1", allow_dot=True), "v1.1")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
cd /workspace/development/frappe-bench
python -m unittest docs.docs.tests.test_slug -v
```

Expected: FAIL with `ModuleNotFoundError` or missing function.

- [ ] **Step 3: 实现 slug 服务**

Create `frappe-bench/apps/docs/docs/docs/services/__init__.py` as an empty file.

Create `frappe-bench/apps/docs/docs/docs/services/slug.py`:

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
cd /workspace/development/frappe-bench
python -m unittest docs.docs.tests.test_slug -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/services frappe-bench/apps/docs/docs/docs/tests/test_slug.py
git commit -m "test: add docs slug service"
```

## Task 4: 创建 DOC0010 和 DOC0011

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0010/doc0010.json`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0010/doc0010.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0010/test_doc0010.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0011/doc0011.json`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0011/doc0011.py`

- [ ] **Step 1: 写 DOC0010 后端测试**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0010/test_doc0010.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase


class TestDOC0010(IntegrationTestCase):
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

		with self.assertRaises(frappe.DuplicateEntryError):
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
```

- [ ] **Step 2: 创建 DOC0011 子表元数据和类**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0011/__init__.py` as an empty file.

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0011/doc0011.py`:

```python
from frappe.model.document import Document


class DOC0011(Document):
	pass
```

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0011/doc0011.json`:

```json
{
 "actions": [],
 "creation": "2026-05-17 00:00:00.000000",
 "doctype": "DocType",
 "editable_grid": 1,
 "engine": "InnoDB",
 "field_order": ["user", "role"],
 "fields": [
  {"fieldname": "user", "fieldtype": "Link", "label": "用户", "options": "User", "reqd": 1},
  {"fieldname": "role", "fieldtype": "Select", "label": "角色", "options": "viewer\neditor\npublisher\nmanager", "reqd": 1}
 ],
 "istable": 1,
 "module": "Docs",
 "name": "DOC0011",
 "owner": "Administrator",
 "permissions": [],
 "sort_field": "modified",
 "sort_order": "DESC",
 "states": [],
 "title": "文档项目成员"
}
```

- [ ] **Step 3: 创建 DOC0010 元数据和类**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0010/__init__.py` as an empty file.

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0010/doc0010.py`:

```python
import frappe
from frappe import _
from frappe.model.document import Document

from docs.docs.services.slug import normalize_slug, validate_slug


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
```

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0010/doc0010.json`:

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "field:slug",
 "creation": "2026-05-17 00:00:00.000000",
 "doctype": "DocType",
 "engine": "InnoDB",
 "field_order": ["title", "slug", "description", "is_public", "default_version", "status", "members"],
 "fields": [
  {"fieldname": "title", "fieldtype": "Data", "in_list_view": 1, "label": "项目标题", "reqd": 1},
  {"fieldname": "slug", "fieldtype": "Data", "in_list_view": 1, "in_standard_filter": 1, "label": "Slug", "reqd": 1, "unique": 1},
  {"fieldname": "description", "fieldtype": "Small Text", "label": "项目说明"},
  {"default": "0", "fieldname": "is_public", "fieldtype": "Check", "in_list_view": 1, "label": "公开访问"},
  {"fieldname": "default_version", "fieldtype": "Link", "label": "默认版本", "options": "DOC0020"},
  {"default": "active", "fieldname": "status", "fieldtype": "Select", "in_list_view": 1, "label": "状态", "options": "active\narchived", "reqd": 1},
  {"fieldname": "members", "fieldtype": "Table", "label": "项目成员", "options": "DOC0011"}
 ],
 "module": "Docs",
 "name": "DOC0010",
 "naming_rule": "By fieldname",
 "owner": "Administrator",
 "permissions": [
  {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "role": "System Manager", "share": 1, "write": 1}
 ],
 "sort_field": "modified",
 "sort_order": "DESC",
 "states": [],
 "title": "文档项目"
}
```

- [ ] **Step 4: 运行 DOC0010 测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.doctype.doc0010.test_doc0010
```

Expected: PASS after the test site is created and app installed in Task 10. Before Task 10, this command may fail because the site or DocType table does not exist.

- [ ] **Step 5: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/doctype/doc0010 frappe-bench/apps/docs/docs/docs/doctype/doc0011
git commit -m "feat: add docs project doctypes"
```

## Task 5: 创建 DOC0020 文档版本

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0020/doc0020.json`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0020/doc0020.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0020/test_doc0020.py`

- [ ] **Step 1: 写 DOC0020 测试**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0020/test_doc0020.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase


class TestDOC0020(IntegrationTestCase):
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
```

- [ ] **Step 2: 实现 DOC0020 类**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0020/doc0020.py`:

```python
import frappe
from frappe import _
from frappe.model.document import Document

from docs.docs.services.slug import normalize_slug, validate_slug


class DOC0020(Document):
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
		existing = frappe.db.exists(
			"DOC0020",
			{"project": self.project, "version_key": self.version_key, "name": ["!=", self.name]},
		)
		if existing:
			frappe.throw(_("同一项目下文档版本 {0} 已存在。").format(self.version_key))

	def ensure_default_version(self):
		has_default = frappe.db.exists("DOC0020", {"project": self.project, "is_default": 1, "name": ["!=", self.name]})
		if not has_default:
			frappe.db.set_value("DOC0020", self.name, "is_default", 1)
			frappe.db.set_value("DOC0010", self.project, "default_version", self.name)

	def clear_other_default_versions(self):
		if not self.is_default:
			return
		for row in frappe.get_all("DOC0020", filters={"project": self.project, "is_default": 1, "name": ["!=", self.name]}):
			frappe.db.set_value("DOC0020", row.name, "is_default", 0)
		frappe.db.set_value("DOC0010", self.project, "default_version", self.name)
```

- [ ] **Step 3: 创建 DOC0020 JSON**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0020/doc0020.json`:

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "format:{project}-{version_key}",
 "creation": "2026-05-17 00:00:00.000000",
 "doctype": "DocType",
 "engine": "InnoDB",
 "field_order": ["project", "version_key", "title", "is_default", "status", "source_version", "creation_mode"],
 "fields": [
  {"fieldname": "project", "fieldtype": "Link", "in_list_view": 1, "in_standard_filter": 1, "label": "文档项目", "options": "DOC0010", "reqd": 1},
  {"fieldname": "version_key", "fieldtype": "Data", "in_list_view": 1, "label": "版本标识", "reqd": 1},
  {"fieldname": "title", "fieldtype": "Data", "in_list_view": 1, "label": "版本标题", "reqd": 1},
  {"default": "0", "fieldname": "is_default", "fieldtype": "Check", "in_list_view": 1, "label": "默认版本"},
  {"default": "draft", "fieldname": "status", "fieldtype": "Select", "in_list_view": 1, "label": "状态", "options": "draft\npublished\narchived", "reqd": 1},
  {"fieldname": "source_version", "fieldtype": "Link", "label": "来源版本", "options": "DOC0020"},
  {"default": "blank", "fieldname": "creation_mode", "fieldtype": "Select", "label": "创建方式", "options": "blank\ncopy", "reqd": 1}
 ],
 "module": "Docs",
 "name": "DOC0020",
 "naming_rule": "Expression",
 "owner": "Administrator",
 "permissions": [
  {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "role": "System Manager", "share": 1, "write": 1}
 ],
 "sort_field": "creation",
 "sort_order": "DESC",
 "states": [],
 "title": "文档版本"
}
```

- [ ] **Step 4: 运行 DOC0020 测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.doctype.doc0020.test_doc0020
```

Expected: PASS after Task 10.

- [ ] **Step 5: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/doctype/doc0020
git commit -m "feat: add document version doctype"
```

## Task 6: 创建 DOC0030 和 DOC0031

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.json`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/test_doc0030.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0031/doc0031.json`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0031/doc0031.py`

- [ ] **Step 1: 写 DOC0030 页面测试**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0030/test_doc0030.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase


class TestDOC0030(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def create_version(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		version = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		return project, version

	def test_root_page_path(self):
		project, version = self.create_version()
		page = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": version.name, "title": "API", "slug": "API"}
		).insert()

		self.assertEqual(page.slug, "api")
		self.assertEqual(page.path, "api")

	def test_child_page_path(self):
		project, version = self.create_version()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": version.name, "title": "API", "slug": "api"}
		).insert()
		child = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"parent_page": parent.name,
				"title": "创建订单",
				"slug": "create-order",
			}
		).insert()

		self.assertEqual(child.path, "api/create-order")

	def test_parent_must_be_same_version(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		v1 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		v2 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v2", "title": "v2"}).insert()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": v1.name, "title": "API", "slug": "api"}
		).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "DOC0030",
					"project": project.name,
					"doc_version": v2.name,
					"parent_page": parent.name,
					"title": "创建订单",
					"slug": "create-order",
				}
			).insert()

	def test_save_creates_revision(self):
		project, version = self.create_version()
		page = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# 创建订单",
			}
		).insert()

		self.assertTrue(page.latest_revision)
		revision = frappe.get_doc("DOC0031", page.latest_revision)
		self.assertEqual(revision.revision_no, 1)
		self.assertEqual(revision.content_markdown, "# 创建订单")
```

- [ ] **Step 2: 创建 DOC0031 类**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0031/doc0031.py`:

```python
import frappe
from frappe import _
from frappe.model.document import Document


class DOC0031(Document):
	def on_trash(self):
		frappe.throw(_("文档页面修订作为编辑历史，不能删除。"))
```

- [ ] **Step 3: 创建 DOC0030 类**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.py`:

```python
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from docs.docs.services.slug import normalize_slug, validate_slug


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
```

- [ ] **Step 4: 创建 DOC0030 和 DOC0031 JSON**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.json`:

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "hash",
 "creation": "2026-05-17 00:00:00.000000",
 "doctype": "DocType",
 "engine": "InnoDB",
 "field_order": ["project", "doc_version", "parent_page", "title", "slug", "path", "doc_type", "content_markdown", "summary", "sort_order", "status", "review_status", "latest_revision"],
 "fields": [
  {"fieldname": "project", "fieldtype": "Link", "in_standard_filter": 1, "label": "文档项目", "options": "DOC0010", "reqd": 1},
  {"fieldname": "doc_version", "fieldtype": "Link", "in_list_view": 1, "in_standard_filter": 1, "label": "文档版本", "options": "DOC0020", "reqd": 1},
  {"fieldname": "parent_page", "fieldtype": "Link", "label": "父页面", "options": "DOC0030"},
  {"fieldname": "title", "fieldtype": "Data", "in_list_view": 1, "label": "页面标题", "reqd": 1},
  {"fieldname": "slug", "fieldtype": "Data", "in_list_view": 1, "label": "Slug", "reqd": 1},
  {"fieldname": "path", "fieldtype": "Data", "in_list_view": 1, "in_standard_filter": 1, "label": "路径", "read_only": 1},
  {"default": "other", "fieldname": "doc_type", "fieldtype": "Select", "label": "文档类型", "options": "api\nmanual\nsdk\nwebhook\nfaq\nerror_code\narchitecture\nchangelog\nother", "reqd": 1},
  {"fieldname": "content_markdown", "fieldtype": "Long Text", "label": "Markdown 内容"},
  {"fieldname": "summary", "fieldtype": "Small Text", "label": "摘要"},
  {"default": "0", "fieldname": "sort_order", "fieldtype": "Int", "label": "排序"},
  {"default": "draft", "fieldname": "status", "fieldtype": "Select", "in_list_view": 1, "label": "状态", "options": "draft\npublished\narchived", "reqd": 1},
  {"default": "draft", "fieldname": "review_status", "fieldtype": "Select", "label": "审核状态", "options": "draft\nreviewing\napproved\nrejected"},
  {"fieldname": "latest_revision", "fieldtype": "Link", "label": "最近修订", "options": "DOC0031", "read_only": 1}
 ],
 "module": "Docs",
 "name": "DOC0030",
 "naming_rule": "Random",
 "owner": "Administrator",
 "permissions": [
  {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "role": "System Manager", "share": 1, "write": 1}
 ],
 "sort_field": "creation",
 "sort_order": "DESC",
 "states": [],
 "title": "文档页面"
}
```

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0031/doc0031.json`:

```json
{
 "actions": [],
 "allow_rename": 0,
 "autoname": "hash",
 "creation": "2026-05-17 00:00:00.000000",
 "doctype": "DocType",
 "engine": "InnoDB",
 "field_order": ["page", "project", "doc_version", "revision_no", "title", "content_markdown", "summary", "change_type", "created_by", "created_at"],
 "fields": [
  {"fieldname": "page", "fieldtype": "Link", "in_standard_filter": 1, "label": "文档页面", "options": "DOC0030", "reqd": 1},
  {"fieldname": "project", "fieldtype": "Link", "label": "文档项目", "options": "DOC0010", "reqd": 1},
  {"fieldname": "doc_version", "fieldtype": "Link", "label": "文档版本", "options": "DOC0020", "reqd": 1},
  {"fieldname": "revision_no", "fieldtype": "Int", "in_list_view": 1, "label": "修订号", "reqd": 1},
  {"fieldname": "title", "fieldtype": "Data", "label": "页面标题", "reqd": 1},
  {"fieldname": "content_markdown", "fieldtype": "Long Text", "label": "Markdown 内容"},
  {"fieldname": "summary", "fieldtype": "Small Text", "label": "摘要"},
  {"default": "manual_save", "fieldname": "change_type", "fieldtype": "Select", "label": "变更类型", "options": "manual_save\nauto_save\nrestore\npublish", "reqd": 1},
  {"fieldname": "created_by", "fieldtype": "Link", "label": "修改人", "options": "User", "read_only": 1},
  {"fieldname": "created_at", "fieldtype": "Datetime", "label": "修改时间", "read_only": 1}
 ],
 "module": "Docs",
 "name": "DOC0031",
 "naming_rule": "Random",
 "owner": "Administrator",
 "permissions": [
  {"create": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "role": "System Manager", "share": 1, "write": 1}
 ],
 "sort_field": "creation",
 "sort_order": "DESC",
 "states": [],
 "title": "文档页面修订"
}
```

- [ ] **Step 5: 运行 DOC0030 测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.doctype.doc0030.test_doc0030
```

Expected: PASS after Task 10.

- [ ] **Step 6: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/doctype/doc0030 frappe-bench/apps/docs/docs/docs/doctype/doc0031
git commit -m "feat: add document page revisions"
```

## Task 7: 添加项目权限服务

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/services/permissions.py`
- Create: `frappe-bench/apps/docs/docs/docs/tests/test_permissions.py`

- [ ] **Step 1: 写权限服务测试**

Create `frappe-bench/apps/docs/docs/docs/tests/test_permissions.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase

from docs.docs.services.permissions import get_project_role, has_project_role


class TestProjectPermissions(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_system_manager_has_manager_role(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		self.assertEqual(get_project_role(project.name, "Administrator"), "manager")

	def test_member_role_is_returned(self):
		project = frappe.get_doc(
			{
				"doctype": "DOC0010",
				"title": "支付系统",
				"slug": frappe.generate_hash(length=8),
				"members": [{"user": "Administrator", "role": "editor"}],
			}
		).insert()
		self.assertTrue(has_project_role(project.name, "Administrator", "viewer"))
		self.assertTrue(has_project_role(project.name, "Administrator", "editor"))
		self.assertFalse(has_project_role(project.name, "Administrator", "publisher"))
```

- [ ] **Step 2: 实现权限服务**

Create `frappe-bench/apps/docs/docs/docs/services/permissions.py`:

```python
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
```

- [ ] **Step 3: 运行权限测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.tests.test_permissions
```

Expected: PASS after Task 10.

- [ ] **Step 4: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/services/permissions.py frappe-bench/apps/docs/docs/docs/tests/test_permissions.py
git commit -m "feat: add docs project permission service"
```

## Task 8: 添加版本复制服务

**Files:**
- Create: `frappe-bench/apps/docs/docs/docs/services/versioning.py`
- Create: `frappe-bench/apps/docs/docs/docs/tests/test_versioning.py`

- [ ] **Step 1: 写版本复制测试**

Create `frappe-bench/apps/docs/docs/docs/tests/test_versioning.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase

from docs.docs.services.versioning import copy_version_tree


class TestVersioningService(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_copy_version_tree_copies_parent_child_paths(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		v1 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		v2 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v2", "title": "v2"}).insert()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": v1.name, "title": "API", "slug": "api"}
		).insert()
		frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": v1.name,
				"parent_page": parent.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# 创建订单",
			}
		).insert()

		copy_version_tree(v1.name, v2.name)

		copied_paths = frappe.get_all("DOC0030", filters={"doc_version": v2.name}, pluck="path")
		self.assertEqual(set(copied_paths), {"api", "api/create-order"})
```

- [ ] **Step 2: 实现版本复制服务**

Create `frappe-bench/apps/docs/docs/docs/services/versioning.py`:

```python
import frappe


def copy_version_tree(source_version: str, target_version: str) -> dict[str, str]:
	source = frappe.get_doc("DOC0020", source_version)
	target = frappe.get_doc("DOC0020", target_version)
	if source.project != target.project:
		frappe.throw("来源版本和目标版本必须属于同一项目。")

	page_map = {}
	pages = frappe.get_all(
		"DOC0030",
		filters={"doc_version": source.name},
		fields=["name"],
		order_by="path asc",
	)

	for row in pages:
		old_page = frappe.get_doc("DOC0030", row.name)
		new_page = frappe.copy_doc(old_page)
		new_page.project = target.project
		new_page.doc_version = target.name
		new_page.parent_page = page_map.get(old_page.parent_page)
		new_page.latest_revision = None
		new_page.insert()
		page_map[old_page.name] = new_page.name

	return page_map
```

- [ ] **Step 3: 运行版本复制测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.tests.test_versioning
```

Expected: PASS after Task 10.

- [ ] **Step 4: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/services/versioning.py frappe-bench/apps/docs/docs/docs/tests/test_versioning.py
git commit -m "feat: add docs version copy service"
```

## Task 9: 添加恢复修订接口

**Files:**
- Modify: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.py`
- Create: `frappe-bench/apps/docs/docs/docs/doctype/doc0030/test_doc0030_restore.py`

- [ ] **Step 1: 写恢复修订测试**

Create `frappe-bench/apps/docs/docs/docs/doctype/doc0030/test_doc0030_restore.py`:

```python
import frappe
from frappe.tests import IntegrationTestCase

from docs.docs.doctype.doc0030.doc0030 import restore_revision


class TestDOC0030Restore(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_restore_revision_updates_draft_and_creates_restore_revision(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		version = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		page = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# old",
			}
		).insert()
		old_revision = page.latest_revision
		page.content_markdown = "# new"
		page.save()

		restore_revision(page.name, old_revision)
		page.reload()

		self.assertEqual(page.content_markdown, "# old")
		restore = frappe.get_doc("DOC0031", page.latest_revision)
		self.assertEqual(restore.change_type, "restore")
		self.assertEqual(restore.content_markdown, "# old")
```

- [ ] **Step 2: 实现恢复接口**

Append to `frappe-bench/apps/docs/docs/docs/doctype/doc0030/doc0030.py`:

```python
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
```

- [ ] **Step 3: 运行恢复测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs --module docs.docs.doctype.doc0030.test_doc0030_restore
```

Expected: PASS after Task 10.

- [ ] **Step 4: Commit**

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs/docs/docs/doctype/doc0030
git commit -m "feat: add document revision restore"
```

## Task 10: 创建隔离测试站点并运行核心验证

**Files:**
- No code files.

- [ ] **Step 1: 创建隔离测试站点**

Run:

```bash
cd /workspace/development/frappe-bench
bench new-site test.localhost --db-root-password 123 --admin-password admin
```

Expected: site is created. If the site already exists and is disposable, skip creation and use the existing `test.localhost`.

- [ ] **Step 2: 安装 docs app**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost install-app docs
```

Expected: app installs and DocType tables are created.

- [ ] **Step 3: 运行全部 docs 测试**

Run:

```bash
cd /workspace/development/frappe-bench
bench --site test.localhost run-tests --app docs
```

Expected: PASS.

- [ ] **Step 4: 同步开发站点 schema**

Run only after the isolated test site passes:

```bash
cd /workspace/development/frappe-bench
bench --site development.localhost install-app docs
bench --site development.localhost migrate
```

Expected: development site installs or migrates successfully. If `docs` is already installed, `install-app` may report that the app is already installed; then run `migrate`.

- [ ] **Step 5: Commit verification adjustments**

If tests required code fixes, commit them:

```bash
cd /workspace/development
git add -f frappe-bench/apps/docs
git commit -m "test: verify docs platform foundation"
```

If no files changed, do not create an empty commit.

## Self-Review Checklist

- Spec coverage: This plan covers `DOC0010`、`DOC0011`、`DOC0020`、`DOC0030`、`DOC0031` and explicitly excludes later MVP subsystems.
- Placeholder scan: The plan does not use TBD/TODO/fill-in placeholders. Code and DocType steps include concrete snippets or complete JSON blocks for the worker to apply.
- Type consistency: `project`、`doc_version`、`parent_page`、`latest_revision`、`version_key`、`content_markdown` names match the approved design document.
- Test discipline: Every behavior-changing task includes a failing test step and an isolated bench validation path.
