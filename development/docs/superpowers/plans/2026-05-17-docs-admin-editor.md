# Docs Admin Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first usable Desk editor page for the `doc` app so users can enter `/desk/docs-admin`, browse project/version/page structure, and edit `DOC0030.content_markdown`.

**Architecture:** Use a standard Frappe Desk Page as the shell and mount a Vue 3 app into it. Keep data access behind whitelisted Python APIs so the same tree/detail/save contracts can later power the external reading UI.

**Tech Stack:** Frappe Framework 16, Desk Page, Vue 3 via Frappe esbuild, Milkdown editor dependency, Python UnitTestCase integration tests.

---

### Task 1: Admin API

**Files:**
- Create: `development/frappe-bench/apps/doc/doc/doc/api/__init__.py`
- Create: `development/frappe-bench/apps/doc/doc/doc/api/admin.py`
- Test: `development/frappe-bench/apps/doc/doc/doc/tests/test_admin_api.py`

- [ ] **Step 1: Write failing API tests**

Create tests that build one project, one version, a root page and a child page, then assert:
- `get_project_spaces()` returns the project with default version.
- `get_page_tree(version)` returns nested children ordered by `sort_order`.
- `get_page_detail(page)` returns title, status and markdown.
- `save_page_content(page, markdown)` updates `DOC0030.content_markdown`.

- [ ] **Step 2: Run failing test**

Run: `bench --site test.localhost run-tests --app doc --module doc.doc.tests.test_admin_api`

Expected: FAIL because `doc.doc.api.admin` does not exist.

- [ ] **Step 3: Implement minimal API**

Implement whitelisted functions:
- `get_project_spaces()`
- `get_versions(project)`
- `get_page_tree(doc_version)`
- `get_page_detail(page)`
- `save_page_content(page, content_markdown)`

Use `frappe.get_all`, `frappe.get_doc`, `frappe.db.set_value`, and return plain dictionaries.

- [ ] **Step 4: Verify API tests pass**

Run: `bench --site test.localhost run-tests --app doc --module doc.doc.tests.test_admin_api`

Expected: PASS.

### Task 2: Desk Page Shell

**Files:**
- Create: `development/frappe-bench/apps/doc/doc/doc/page/docs_admin/__init__.py`
- Create: `development/frappe-bench/apps/doc/doc/doc/page/docs_admin/docs_admin.json`
- Create: `development/frappe-bench/apps/doc/doc/doc/page/docs_admin/docs_admin.js`
- Modify: `development/frappe-bench/apps/doc/doc/desktop_icon/doc.json`
- Modify: `development/frappe-bench/apps/doc/doc/hooks.py`

- [ ] **Step 1: Create Page fixture and shell script**

Create standard Page `docs-admin` titled `文档编辑器`. In JS, create a single-column app page, append `<div class="docs-admin-app"></div>`, require `docs_admin.bundle.js`, and mount `frappe.ui.setup_docs_admin`.

- [ ] **Step 2: Point entry links to the page**

Set Desktop Icon link to `/desk/docs-admin`, and set `add_to_apps_screen` route to `/desk/docs-admin`.

- [ ] **Step 3: Migrate isolated test site**

Run: `bench --site test.localhost migrate`

Expected: PASS and page exists.

### Task 3: Vue Editor Bundle

**Files:**
- Create: `development/frappe-bench/apps/doc/doc/public/js/docs_admin/docs_admin.bundle.js`
- Create: `development/frappe-bench/apps/doc/doc/public/js/docs_admin/DocsAdmin.vue`
- Create: `development/frappe-bench/apps/doc/doc/public/css/docs_admin.bundle.css`
- Modify: `development/frappe-bench/apps/doc/doc/hooks.py`

- [ ] **Step 1: Implement Vue app**

Build a compact work UI:
- Top row project and version selects.
- Left tree reusing the API tree shape.
- Main editor header with title/status and save button.
- Milkdown-backed markdown editor when available; fallback textarea with the same `contentMarkdown` model if dependency loading fails.

- [ ] **Step 2: Add Desk CSS**

Add quiet enterprise styling: fixed left tree, readable editor surface, no decorative hero/card nesting.

- [ ] **Step 3: Build assets**

Run: `bench build --apps doc`

Expected: `docs_admin.bundle.js` and CSS are emitted and assets map updated.

### Task 4: Full Verification And Commit

**Files:**
- All changed files above.

- [ ] **Step 1: Run app tests**

Run: `bench --site test.localhost run-tests --app doc`

Expected: all existing and new tests pass.

- [ ] **Step 2: Sync development site**

Run: `bench --site development.localhost migrate`

Expected: migrate succeeds, `Page docs-admin` and `Desktop Icon Doc` point to the editor.

- [ ] **Step 3: Clear cache**

Run: `bench --site development.localhost clear-cache`

- [ ] **Step 4: Commit**

Stage only source, fixture, docs, and built asset files for the `doc` app. Do not stage `__pycache__` or `.pyc`.

Commit message: `feat: add docs admin editor page`

---

**Self-review:** This plan covers the confirmed first editor slice: Desk entry, reusable APIs, Vue/Milkdown editor shell, save flow, migration and tests. It intentionally excludes external reading pages, private share links, Mermaid, draw.io, publish workflow UI, and diff viewer.
