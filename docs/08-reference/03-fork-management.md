---
title: Fork Management
---

# Fork Management Best Practices

## Initial Fork Setup

```bash
# 1. Fork on GitHub (use the Fork button)

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/frappe_docker
cd frappe_docker

# 3. Add upstream remote (original repo)
git remote add upstream https://github.com/frappe/frappe_docker.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR_USERNAME/frappe_docker (your fork)
# upstream  https://github.com/frappe/frappe_docker (original)

# 5. Create development branch
git checkout -b my-custom-setup
```

## Safe Customization Zones

**✅ Safe (Won't conflict with upstream):**

```
development/                    # Your entire dev environment
  ├── frappe-bench/            # Local installation
  └── .vscode/                 # Your editor settings

compose.my-*.yaml              # Your custom compose overrides
scripts/my-*.sh                # Your custom scripts
docs/my-*.md                   # Your custom documentation
.env.local                     # Local environment overrides
.gitignore.local              # Additional gitignore rules
```

**⚠️ Modification Needed (May conflict):**

```
compose.yaml                   # Core - use overrides instead
docker-bake.hcl               # Build config - use custom files
images/*/Dockerfile           # Core images - extend rather than modify
```

**❌ Never Modify (Will break upstream sync):**

```
.github/workflows/            # CI/CD pipelines
images/*/                     # Core image definitions
resources/                    # Core templates
```

## Keeping Fork Updated

<!-- transinfosh:start -->

::: info TransInfoSH 定制
官方本节给出的同步流程本来就是合并上游后直接推送 fork，不要求每次创建 Pull
Request。`transinfosh/frappe_docker` 沿用这个方式：先在独立 worktree 或干净
分支中合并并验证，再直接更新 `main`。只有出现复杂冲突、基础运行时大版本变更或
需要评审时，才临时使用 Pull Request。不得把
`development/frappe-bench/apps/` 中的应用源码带入同步提交。
:::

<!-- transinfosh:end -->

```bash
# Regularly sync with upstream (weekly recommended)
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Update your development branch
git checkout my-custom-setup
git rebase main  # Or: git merge main

# If conflicts occur during rebase:
# 1. Fix conflicts in files
# 2. git add <fixed-files>
# 3. git rebase --continue
# Or: git rebase --abort  (to cancel)
```

<!-- transinfosh:start -->

对于 TransInfoSH fork，推送前还应确认远端没有新提交，并只做快进更新：

```bash
git fetch origin
git fetch upstream
git merge upstream/main
git push origin main
```

若 `origin/main` 已变化，应先重新获取并整合，不要使用强制推送覆盖远端。

<!-- transinfosh:end -->

## Custom Environment Pattern

Create override files for your customizations:

```yaml
# compose.my-env.yaml
version: "3.7"

services:
  backend:
    environment:
      # Your custom environment variables
      - DEVELOPER_MODE=true
      - MY_API_KEY=${MY_API_KEY}
    volumes:
      # Your custom bind mounts
      - ./development/my-scripts:/home/frappe/my-scripts
      - ./development/my-config:/home/frappe/config

  # Your additional services
  my-monitoring:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
# Use it:
# docker compose -f compose.yaml -f compose.my-env.yaml up
```

## .gitignore Strategy

Add to `.gitignore` (or create `.gitignore.local`):

```gitignore
# Local environment files
.env.local
*.local.yaml
compose.my-*.yaml

# Development artifacts
development/frappe-bench/sites/*
development/frappe-bench/apps/*
!development/frappe-bench/apps.json
development/frappe-bench/logs/
development/frappe-bench/env/

# Local customizations
my-local-configs/
scripts/my-*.sh
docs/internal-*.md

# IDE
.vscode/settings.json.local
.idea/

# Temporary files
*.swp
*.swo
*~
.DS_Store
```

## Contributing Back to Upstream

```bash
# 1. Create feature branch from main
git checkout main
git pull upstream main
git checkout -b feature/my-improvement

# 2. Make changes and commit
git add .
git commit -m "feat: add awesome feature"

# 3. Push to YOUR fork
git push origin feature/my-improvement

# 4. Create Pull Request on GitHub
# Go to: https://github.com/frappe/frappe_docker
# Click "Compare & pull request"
```
