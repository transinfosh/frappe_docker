ARG FRAPPE_BRANCH=version-16
ARG FRAPPE_IMAGE_PREFIX=frappe
ARG FRAPPE_IMAGE_TAG=version-16

FROM ${FRAPPE_IMAGE_PREFIX}/build:${FRAPPE_IMAGE_TAG} AS builder

ARG FRAPPE_BRANCH=version-16
ARG FRAPPE_PATH=https://github.com/frappe/frappe
ARG CACHE_BUST=""

USER frappe

RUN --mount=type=secret,id=framework_apps_json,target=/opt/frappe/framework-apps.json,uid=1000,gid=1000 \
  --mount=type=secret,id=source_token,required=false,uid=1000,gid=1000 \
  : "${CACHE_BUST}" && \
  source_token="$(cat /run/secrets/source_token 2>/dev/null || true)" && \
  if [ -n "${source_token}" ]; then \
    python3 -c 'import json; print("\n".join(app["url"] for app in json.load(open("/opt/frappe/framework-apps.json"))))' | \
      while IFS= read -r app_url; do \
        case "${app_url}" in \
          https://github.com/*) \
            repo_path="${app_url#https://github.com/}"; \
            repo_path="${repo_path%%/*}/"; \
            app_url="https://github.com/${repo_path}"; \
            git config --global \
              url."https://x-access-token:${source_token}@github.com/${repo_path}".insteadOf \
              "${app_url}"; \
            ;; \
        esac; \
      done; \
  fi && \
  bench init --apps_path=/opt/frappe/framework-apps.json \
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
  find apps -mindepth 2 -type d -name __pycache__ -prune -exec rm -rf {} + && \
  find apps -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

FROM ${FRAPPE_IMAGE_PREFIX}/base:${FRAPPE_IMAGE_TAG}

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
