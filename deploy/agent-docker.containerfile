ARG VERSION=latest
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/inginious/core-base:${VERSION}

ARG SCM_VERSION

COPY inginious/agent/__init__.py inginious/agent/
COPY inginious/agent/docker_agent/ inginious/agent/docker_agent/
COPY inginious/scripts inginious/scripts

RUN dnf install -y gcc python3.11-devel

# See https://github.com/pypa/setuptools_scm/#usage-from-docker
RUN --mount=source=.git,target=.git,type=bind \
    if [ -n "$SCM_VERSION" ]; then \
      export SETUPTOOLS_SCM_PRETEND_VERSION="$SCM_VERSION" ; \
    fi && \
    pip3 install --no-cache-dir -e .

CMD ["sh", "-c", "python3 -m inginious.scripts.agent_docker ${BACKEND} --tmpdir=/tmp/agent_data/ ${EXTRA_AGENT_DOCKER_ARGS}"]
