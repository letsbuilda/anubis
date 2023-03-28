FROM --platform=linux/amd64 python:3.11-slim@sha256:2f749ef90f54fd4b3c77cde78eec23ab5b8199d9ac84e4ced6ae523ef223ef7b

# Define Git SHA build argument for sentry
ARG git_sha="development"

COPY . .

RUN pip install .

CMD ["python", "-m", "bot"]
