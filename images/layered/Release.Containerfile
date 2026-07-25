ARG FRAPPE_BRANCH=version-16
ARG FRAPPE_IMAGE_PREFIX=frappe

FROM ${FRAPPE_IMAGE_PREFIX}/build:${FRAPPE_BRANCH} AS builder

ARG FRAPPE_BRANCH=version-16
ARG FRAPPE_PATH=https://github.com/frappe/frappe
ARG CACHE_BUST=""

USER frappe

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
            git config --global \
              url."https://x-access-token:${token}@github.com/${repo_path}".insteadOf \
              "${app_url}"; \
            ;; \
        esac; \
      done; \
  fi && \
  export APP_INSTALL_ARGS="" && \
  if [ -s /opt/frappe/apps.json ]; then \
    export APP_INSTALL_ARGS="--apps_path=/opt/frappe/apps.json"; \
  fi && \
  bench init ${APP_INSTALL_ARGS} \
    --frappe-branch=${FRAPPE_BRANCH} \
    --frappe-path=${FRAPPE_PATH} \
    --no-procfile \
    --no-backups \
    --skip-redis-config-generation \
    --verbose \
    /home/frappe/frappe-bench && \
  rm -f "${HOME}/.gitconfig" && \
  cd /home/frappe/frappe-bench && \
  echo "{}" > sites/common_site_config.json && \
  find apps -mindepth 1 -path "*/.git" -prune -exec rm -rf {} + && \
  find apps -mindepth 2 -type d \( -name node_modules -o -name __pycache__ \) -prune -exec rm -rf {} + && \
  find apps -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

FROM ${FRAPPE_IMAGE_PREFIX}/base:${FRAPPE_BRANCH} AS backend

ARG RUNTIME_APT_PACKAGES=""

USER root

RUN if [ -n "${RUNTIME_APT_PACKAGES}" ]; then \
    apt-get update && \
    apt-get install --no-install-recommends -y ${RUNTIME_APT_PACKAGES} && \
    rm -rf /var/lib/apt/lists/*; \
  fi

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

RUN cp -r /home/frappe/frappe-bench/sites/assets /home/frappe/frappe-bench/assets && \
  rm -rf /home/frappe/frappe-bench/sites/assets

VOLUME [ \
  "/home/frappe/frappe-bench/sites", \
  "/home/frappe/frappe-bench/logs" \
]

USER root

COPY resources/core/main-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

COPY resources/core/start.sh /usr/local/bin/start.sh
RUN chmod 755 /usr/local/bin/start.sh

USER frappe
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["start.sh"]
