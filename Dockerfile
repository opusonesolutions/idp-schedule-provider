FROM python:3.7-slim as requirements_export
RUN pip install poetry
COPY poetry.lock .
COPY pyproject.toml .
RUN poetry export -o requirements.txt

# Use an official Python runtime as a base image
FROM python:3.7-slim

# Set the working directory to /app
WORKDIR /usr/src
# launch the webserver
ENTRYPOINT [ "docker_scripts/init.sh" ]

# Install any needed packages specified in requirements.txt
COPY --from=requirements_export requirements.txt /usr/src
RUN pip install -r requirements.txt --no-cache-dir

ADD . /usr/src

# For when run as nobody in environments on AWS
RUN chown -R nobody:nogroup /usr/src
