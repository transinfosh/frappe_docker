ARG FRAMEWORK_IMAGE

FROM ${FRAMEWORK_IMAGE}

ARG APP_NAME
ARG CACHE_BUST=""

USER frappe

WORKDIR /home/frappe/frappe-bench

RUN --mount=type=secret,id=apps_json,target=/opt/frappe/apps.json,uid=1000,gid=1000 \
  --mount=type=secret,id=current_repo_token,required=false,uid=1000,gid=1000 \
  --mount=type=secret,id=source_token,required=false,uid=1000,gid=1000 \
  : "${CACHE_BUST}" && \
  source_token="$(cat /run/secrets/source_token 2>/dev/null || true)" && \
  current_repo_token="$(cat /run/secrets/current_repo_token 2>/dev/null || true)" && \
  token="${source_token:-${current_repo_token}}" && \
  if [ -n "${token}" ]; then \
    if [ -n "${source_token}" ]; then \
      python3 -c 'import json; print("\n".join(app["url"] for app in json.load(open("/opt/frappe/apps.json"))))'; \
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
  python3 -c 'import json; print("\n".join("{} {}".format(app["url"], app["branch"]) for app in json.load(open("/opt/frappe/apps.json"))))' | \
    while IFS=' ' read -r app_url app_branch; do \
      bench get-app --skip-assets --branch "${app_branch}" "${app_url}"; \
    done && \
  rm -f "${HOME}/.gitconfig" && \
  ln -s ../assets sites/assets && \
  bench build --app "${APP_NAME}" && \
  rm sites/assets && \
  find apps -mindepth 1 -path "*/.git" -prune -exec rm -rf {} + && \
  find apps -mindepth 2 -type d -name __pycache__ -prune -exec rm -rf {} + && \
  find apps -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
