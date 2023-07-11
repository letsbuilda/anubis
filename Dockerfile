FROM python:3.11-slim@sha256:1966141ab594e175852a033da2a38f0cb042b5b92896c22073f8477f96f43b06

# Define Git SHA build argument for sentry
ARG git_sha="development"
ENV GIT_SHA=$git_sha

COPY requirements.txt .
RUN python -m pip install --requirement requirements.txt

COPY . .
RUN python -m pip install .

RUN adduser --disabled-password bot
USER bot

CMD ["python", "-m", "bot"]
