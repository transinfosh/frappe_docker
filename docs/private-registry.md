# 通用镜像发布与自建仓库

应用镜像先由 GitHub Actions 完成构建与验证、发布到 GHCR，再自动同步到 `registry.trinfo.net`。仓库在公司 2.52 运维服务器，通过公网 HTTPS 和 FRP 提供访问，镜像数据存储在独立数据盘。

## Frappe 应用

统一调用 `.github/workflows/app-release-image.yml`。该工作流已经包含构建、验证、GHCR 发布和后置同步，无需在应用仓库单独编写同步 job。使用固定提交 SHA，沿用各应用已有的构建参数，并传入：

```yaml
secrets:
  APP_SOURCE_TOKEN: ${{ secrets.APP_SOURCE_TOKEN }}
  REGISTRY_USERNAME: ${{ secrets.REGISTRY_USERNAME }}
  REGISTRY_PASSWORD: ${{ secrets.REGISTRY_PASSWORD }}
```

也可以对受信任的同组织公共工作流使用 `secrets: inherit`。

## Frappe 基础镜像

`.github/workflows/framework-base-image.yml` 同样在构建与 GHCR 发布成功后调用通用同步模块，按精确的 `image_tag` 发布 `tsuite-base`。

## 其他镜像构建流程

在镜像成功发布后调用 `.github/workflows/mirror-release-image.yml`，传入 `image_name`（不带 tag 的完整源仓库地址）和 `image_tag`（精确 tag），以及上述两个 Registry secrets。它不依赖 Frappe、DocType 或具体构建技术，支持 GHCR 与 Docker Hub 等标准镜像源，也可以手动触发来回填已有版本。`release_tag` 保留兼容 Frappe 发布，数值版本的前导 v 会去除；其他流程优先使用不做改写的 `image_tag`。

当前共享流程固定版本为 `8957f9148e1eff3e43dbf3e2ab2330a430086764`。

同步保留 namespace、镜像名与版本号，例如 `ghcr.io/transinfosh/my_app:1.2.3` 对应 `registry.trinfo.net/transinfosh/my_app:1.2.3`。按源 digest 复制所有平台并核对目标 digest；断开的上传可以启动新会话重试，已完成的层会复用。同步失败可以单独重跑，不需要重新构建。

默认同时同步 GHCR 中与本次版本摘要相同的其他标签，包括 latest 和 Git 提交别名；写入前再次核对源标签。其他镜像源只检查 latest、stable 常用别名。可设置 `mirror_aliases: false` 仅同步精确标签。

## 独立服务构建

`transinfosh/tsuite_deploy` 的新版 `.github/workflows/build-images.yml` 已包含后置同步，支持 tai-service、tbi-engine、tai-auth。新的调用方除 APP_SOURCE_TOKEN 外，还须显式传入 REGISTRY_USERNAME、REGISTRY_PASSWORD 两项 Secrets。旧提交固定的构建调用保留原契约，可在调用方追加公共同步 job；独立服务的 v 前缀标签须通过 `image_tag` 原样传递。

## 新应用接入

组织级 `REGISTRY_USERNAME`、`REGISTRY_PASSWORD` 已配置为允许全部现有与未来仓库使用。GitHub Free 的私有仓库不能读取组织级 Secrets，需在维护工作区执行统一接入命令：

```bash
python3 resources/registry/enroll.py transinfosh/my_app
```

该脚本位于 frappe_docker；tsuite/Frappe Bench 工作区也保留 `scripts/registry/enroll.py` 入口。脚本读取组织与仓库状态：公开仓库直接继承组织配置；Free 私有仓库自动配置同名仓库 Secrets。需具备相应 GitHub 管理授权，并能通过 SSH 读取 2.52 root 私有的发布凭据。脚本不显示密码或将密码保存在维护机文件中；重复接入已有仓库不会覆盖凭据。轮换凭据时使用 `--refresh` 更新私有仓库副本。

不要把发布凭据交给客户。客户使用只读账号，部署配置必须明确改成自建仓库地址。常用第三方镜像由维护脚本按版本导入，不会因为配置了仓库而自动缓存所有上游。

## 客户部署与 AI 直接维护 Compose

默认使用 `registry.trinfo.net` 与 `registry-pull` 只读账号。构建 job 与后置同步均成功后，
将部署的 `CUSTOM_IMAGE` 或各服务的 `image` 改为自建地址，保留原版本或 digest：

```dotenv
CUSTOM_IMAGE=registry.trinfo.net/transinfosh/quality
CUSTOM_TAG=0.0.31
POSTGRES_IMAGE=registry.trinfo.net/library/postgres:15.17
REDIS_IMAGE=registry.trinfo.net/library/redis:8.6-alpine
```

本 fork 的 PostgreSQL、Redis overrides 默认从自建仓库读取；上述两个依赖变量可以显式覆盖。
已有环境先确认数据库、Redis 的实际版本，把同版本同步并填写变量，避免套用新安装默认值。
密码只通过 `docker login --password-stdin` 输入，不保存在 `.env` 或 Compose 中。

部署前使用现场全部 Compose 参数执行 `docker compose config --images`，确认应用、后台任务、
Redis、数据库及独立服务均来自自建仓库且 manifest 可读取。可使用
[tsuite_deploy 的镜像检查器](https://github.com/transinfosh/tsuite_deploy/blob/main/tools/check-registry-images.py)。
缺少原版本时先补齐，不自动回源或改成 latest；将仓库域名加入 Docker daemon 和命令环境的 `NO_PROXY`。

AI 直接维护现场 Compose 也沿用
[部署镜像来源契约](https://github.com/transinfosh/tsuite_deploy/blob/main/shared/contracts/README.md#镜像来源)，
先备份再修改来源，保留项目、卷、网络和 Secret。仅更新配置不代表已运行容器已经切换，
需要在部署记录中分别说明；正常升级按原流程执行备份、迁移和健康检查。
