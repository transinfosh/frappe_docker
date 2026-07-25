---
title: Custom Apps
---

# Frappe Custom Applications

<!-- transinfosh:start -->

## TransInfoSH 应用仓库约定

::: info TransInfoSH 定制
本 fork 只管理容器、开发环境和镜像构建配置，不跟踪
`development/frappe-bench/apps/` 下的任何应用源码。SRM、Quality、
Project Management、TBI 和 TBI Engine 等业务应用分别使用独立 Git 仓库；
需要安装或构建时，通过应用仓库 URL 与分支或标签明确指定版本。

发布应用镜像时，应在对应应用仓库中维护 GitHub Actions 工作流，并复用本仓库的
镜像构建能力。这样更新单个应用不会把其他应用的工作目录重新提交到
`frappe_docker`。
:::

<!-- transinfosh:end -->

## What Are Frappe Custom Apps?

Custom apps are self-contained, modular business applications that extend Frappe's functionality. They follow a convention-over-configuration approach where the framework provides most boilerplate automatically.

## Custom App Structure

```
my_custom_app/
├── hooks.py                          # App configuration and hooks into Frappe lifecycle
├── modules.txt                       # List of business modules in this app
├── my_custom_app/
│   ├── __init__.py
│   ├── config/
│   │   └── desktop.py                # Desktop workspace icons and shortcuts
│   ├── my_module/                    # Business domain module (e.g., sales, inventory)
│   │   ├── doctype/                  # Document Types (data models)
│   │   │   ├── customer/
│   │   │   │   ├── customer.py       # Python controller (business logic)
│   │   │   │   ├── customer.json     # Model definition (schema, validation)
│   │   │   │   └── customer.js       # Frontend logic (UI interactions)
│   │   └── page/                     # Custom pages (dashboards, reports)
│   ├── public/                       # Static assets (CSS, JS, images)
│   ├── templates/                    # Jinja2 templates for web pages
│   └── www/                          # Web pages accessible via routes
└── requirements.txt                  # Python package dependencies
```

## Built-in Features (Auto-generated)

Every Frappe app automatically includes:

- **REST API** - Automatic CRUD endpoints from DocType definitions
- **Permissions system** - Row-level and field-level access control
- **Audit trails** - Automatic version tracking and change history
- **Custom fields** - Runtime field additions without code changes
- **Workflows** - Configurable approval and state management
- **Reports** - Query builder and report designer
- **Print formats** - PDF generation with custom templates
- **Email integration** - Template-based email sending
- **File attachments** - Document attachment management

## Creating Custom Apps

```bash
# Enter the development container
docker exec -it <container_name> bash

# Create new app (interactive prompts will ask for details)
bench new-app my_custom_app

# Install app to a site
bench --site mysite.com install-app my_custom_app

# Create a new DocType (data model)
bench --site mysite.com console
>>> bench.new_doc("DocType", {...})
# Or use the web UI: Setup → Customize → DocType → New
```
