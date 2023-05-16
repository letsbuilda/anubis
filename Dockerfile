FROM --platform=linux/amd64 python:3.11-slim@sha256:551c9529e77896518ac5693d7e98ee5e12051d625de450ac2a68da1eae15ec87

# Define Git SHA build argument for sentry
ARG git_sha="development"

COPY . .

RUN pip install .

CMD ["python", "-m", "bot"]
