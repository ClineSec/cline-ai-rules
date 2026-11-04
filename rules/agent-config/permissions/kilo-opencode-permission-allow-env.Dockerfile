FROM node:22-slim
RUN npm install -g opencode-ai@1.19.4
# ruleid: kilo-opencode-permission-allow-env
ENV OPENCODE_PERMISSION='{"edit":"allow","bash":"allow"}'
# ruleid: kilo-opencode-permission-allow-env
ENV KILO_PERMISSION {"*":"allow"}
# ok: kilo-opencode-permission-allow-env
ENV OPENCODE_DISABLE_AUTOUPDATE=1
WORKDIR /work
