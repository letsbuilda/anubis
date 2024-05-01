FROM python:3.12-slim@sha256:2be8daddbb82756f7d1f2c7ece706aadcb284bf6ab6d769ea695cc3ed6016743

# Define Git SHA build argument for Sentry
ARG git_sha="development"
ENV GIT_SHA=$git_sha

COPY requirements/requirements.txt .
RUN python -m pip install --requirement requirements.txt

COPY pyproject.toml pyproject.toml
COPY src/ src/
RUN python -m pip install .

RUN adduser --disabled-password bot
USER bot

CMD [ "python", "-m", "bot" ]
