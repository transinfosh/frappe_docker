ARG FRAMEWORK_IMAGE=frappe/base:version-16

FROM ${FRAMEWORK_IMAGE} AS builder

ARG APP_NAME
ARG BUILD_APPS=""
ARG CACHE_BUST=""
USER frappe

WORKDIR /home/frappe/frappe-bench

RUN --mount=type=secret,id=apps_json,target=/opt/frappe/apps.json,uid=1000,gid=1000 \
  --mount=type=secret,id=packages_json,target=/opt/frappe/packages.json,uid=1000,gid=1000 \
  --mount=type=secret,id=current_repo_token,required=false,uid=1000,gid=1000 \
  --mount=type=secret,id=source_token,required=false,uid=1000,gid=1000 \
  : "${CACHE_BUST}" && \
  source_token="$(cat /run/secrets/source_token 2>/dev/null || true)" && \
  current_repo_token="$(cat /run/secrets/current_repo_token 2>/dev/null || true)" && \
  token="${source_token:-${current_repo_token}}" && \
  if [ -n "${token}" ]; then \
    if [ -n "${source_token}" ]; then \
      python3 -c 'import json; print("\n".join(item["url"] for path in ("/opt/frappe/apps.json", "/opt/frappe/packages.json") for item in json.load(open(path))))'; \
    else \
      python3 -c 'import json; print(json.load(open("/opt/frappe/apps.json"))[0]["url"])'; \
    fi | \
      while IFS= read -r app_url; do \
        case "${app_url}" in \
          https://github.com/*) \
            repo_path="${app_url#https://github.com/}"; \
            if [ -n "${source_token}" ]; then \
              repo_path="${repo_path%%/*}/"; \
              app_url="https://github.com/${repo_path}"; \
            fi; \
            git config --global \
              url."https://x-access-token:${token}@github.com/${repo_path}".insteadOf \
              "${app_url}"; \
            ;; \
        esac; \
      done; \
  fi && \
  mkdir -p packages && \
  python3 -c 'import json; print("\n".join("{} {}".format(package["url"], package["branch"]) for package in json.load(open("/opt/frappe/packages.json"))))' | \
    while IFS=' ' read -r package_url package_branch; do \
      [ -n "${package_url}" ] || continue; \
      package_name="${package_url##*/}"; \
      package_name="${package_name%.git}"; \
      git clone --depth 1 --branch "${package_branch}" "${package_url}" "packages/${package_name}"; \
    done && \
  python3 -c 'import json; print("\n".join("{} {}".format(app["url"], app["branch"]) for app in json.load(open("/opt/frappe/apps.json"))))' | \
    while IFS=' ' read -r app_url app_branch; do \
      bench get-app --skip-assets --branch "${app_branch}" "${app_url}"; \
    done && \
  rm -f "${HOME}/.gitconfig" && \
  ln -s ../assets sites/assets && \
  for app in ${BUILD_APPS:-${APP_NAME}}; do bench build --app "${app}"; done && \
  rm sites/assets && \
  find apps packages -mindepth 1 -path "*/.git" -prune -exec rm -rf {} + && \
  find apps -mindepth 2 -type d -name __pycache__ -prune -exec rm -rf {} + && \
  find apps -type d -name node_modules -prune -exec rm -rf {} + && \
  find apps -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

FROM ${FRAMEWORK_IMAGE}

ARG RUNTIME_APT_PACKAGES=""

USER root

RUN if [ -n "${RUNTIME_APT_PACKAGES}" ]; then \
      apt-get update && \
      apt-get install -y --no-install-recommends ${RUNTIME_APT_PACKAGES} && \
      rm -rf /var/lib/apt/lists/*; \
    fi

USER frappe

WORKDIR /home/frappe/frappe-bench

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench/apps ./apps
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench/packages ./packages
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench/assets ./assets
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench/sites/apps.txt ./sites/apps.txt

RUN rm -rf sites/assets && ln -s ../assets sites/assets
