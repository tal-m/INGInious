ARG VERSION=latest
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/inginious/core-base:${VERSION}

ARG SCM_VERSION

COPY inginious/frontend inginious/frontend/
COPY inginious/client inginious/client/
COPY inginious/scripts inginious/scripts

RUN dnf install -y git gcc python3.11-devel

# See https://github.com/pypa/setuptools_scm/#usage-from-docker
RUN --mount=source=.git,target=.git,type=bind \
    if [ -n "$SCM_VERSION" ]; then \
      export SETUPTOOLS_SCM_PRETEND_VERSION="$SCM_VERSION" ; \
    fi && \
    pip3 install --no-cache-dir -e .

RUN pip3 install --upgrade python-keycloak    
    
COPY deploy/db_setup.py /tmp/db_setup.py

CMD ["sh", "-c", "python3 /tmp/db_setup.py; python3 -m inginious.scripts.webapp"]
