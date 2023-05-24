FROM --platform=linux/amd64 python:3.11-slim@sha256:eaee5f73efa9ae962d2077756292bc4878c04fcbc13dc168bb00cc365f35647e

# Define Git SHA build argument for sentry
ARG git_sha="development"

COPY . .

RUN pip install .

CMD ["python", "-m", "bot"]
