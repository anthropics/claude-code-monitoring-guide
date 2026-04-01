FROM ghcr.io/berriai/litellm:main-v1.82.3-stable.patch.2

COPY --from=host-aws-config / /root/.aws
