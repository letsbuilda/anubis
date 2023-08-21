FROM python:3.11-slim@sha256:17d62d681d9ecef20aae6c6605e9cf83b0ba3dc247013e2f43e1b5a045ad4901

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
