FROM python:3.11-slim@sha256:c4992301d47a4f1d3e73c034494c080132f9a4090703babfcfa3317f7ba54461

# Define Git SHA build argument for sentry
ARG git_sha="development"
ENV GIT_SHA=$git_sha

COPY requirements/requirements.txt .
RUN python -m pip install --requirement requirements.txt

COPY . .
RUN python -m pip install .

RUN adduser --disabled-password bot
USER bot

CMD ["python", "-m", "bot"]
