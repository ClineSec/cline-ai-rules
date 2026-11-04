# Image for the standalone-fastmcp contrib servers (notes and Docker helpers).
# Build: docker build -f deploy/contrib.Dockerfile -t devtools-contrib:dev .
FROM python:3.12-slim

WORKDIR /srv/devtools
COPY pyproject.toml ./
COPY contrib ./contrib
RUN pip install --no-cache-dir "fastmcp>=4.1.3"

# The server has to listen on the container's own interface for a published port to reach
# it; who can reach that port is decided by the compose file or the docker run command.
ENV FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=8812 \
    FASTMCP_LOG_LEVEL=INFO

EXPOSE 8812
CMD ["fastmcp", "run", "contrib/notes_server.py:notes", "--transport", "http", "--host", "0.0.0.0", "--port", "8812"]
