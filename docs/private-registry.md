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

## 其他镜像构建流程

在镜像成功发布后调用 `.github/workflows/mirror-release-image.yml`，传入 `image_name`（不带 tag 的完整源仓库地址）和 `image_tag`（精确 tag），以及上述两个 Registry secrets。它不依赖 Frappe、DocType 或具体构建技术，支持 GHCR 与 Docker Hub 等标准镜像源，也可以手动触发来回填已有版本。`release_tag` 保留兼容 Frappe 发布，数值版本的前导 v 会去除；其他流程优先使用不做改写的 `image_tag`。

同步保留 namespace、镜像名与版本号，例如 `ghcr.io/transinfosh/my_app:1.2.3` 对应 `registry.trinfo.net/transinfosh/my_app:1.2.3`。按源 digest 复制所有平台并核对目标 digest；断开的上传可以启动新会话重试，已完成的层会复用。同步失败可以单独重跑，不需要重新构建。

## 新应用接入

组织级 `REGISTRY_USERNAME`、`REGISTRY_PASSWORD` 已配置为允许全部现有与未来仓库使用。GitHub Free 的私有仓库不能读取组织级 Secrets，需在维护工作区执行统一接入命令：

```bash
python3 resources/registry/enroll.py transinfosh/my_app
```

该脚本位于 frappe_docker；tsuite/Frappe Bench 工作区也保留 `scripts/registry/enroll.py` 入口。脚本读取组织与仓库状态：公开仓库直接继承组织配置；Free 私有仓库自动配置同名仓库 Secrets。需具备相应 GitHub 管理授权，并能通过 SSH 读取 2.52 root 私有的发布凭据。脚本不显示密码或将密码保存在维护机文件中；重复接入已有仓库不会覆盖凭据。轮换凭据时使用 `--refresh` 更新私有仓库副本。

不要把发布凭据交给客户。客户使用只读账号，部署配置必须明确改成自建仓库地址。常用第三方镜像由维护脚本按版本导入，不会因为配置了仓库而自动缓存所有上游。
