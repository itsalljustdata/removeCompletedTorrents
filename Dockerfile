ARG BASE_IMAGE=python:3.11-slim

FROM $BASE_IMAGE as base
ARG BASE_IMAGE
FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --disable-pip-version-check --prefix=/install --requirement /requirements.txt --compile

FROM base as final
ARG BASE_IMAGE

RUN apt update \
    && apt install curl wget iputils-ping iproute2 procps -y \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove -y \
    && rm -Rf /var/cache/apt

COPY --from=builder /install /usr/local
COPY rootfs /
ARG uname=iajd \
gname=iajd \
uid=1000 \
gid=1000 

RUN \
 groupadd --gid ${gid} ${gname} && \ 
 useradd --home-dir /home/${uname} -g ${gname} --shell /bin/bash --create-home --uid ${uid} ${uname} && \
 chown -R ${uid}:${gid} /app

HEALTHCHECK --interval=1m --timeout=3s \
  CMD /app/healthcheck.sh

WORKDIR /app

CMD ["bash", "-c", "~/entrypoint.sh"]
