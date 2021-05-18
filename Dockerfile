FROM python:3.7-slim as requirements_export
RUN pip install poetry
COPY poetry.lock .
COPY pyproject.toml .
RUN poetry export -o requirements.txt

# Use an official Python runtime as a base image
FROM python:3.7-slim

# Set the working directory to /app
WORKDIR /app
# launch the webserver
ENTRYPOINT ["uvicorn idp_schedule_provider.main:app"]

# Make port 8000 available to the world outside this container by default
EXPOSE 8000

# Install any needed packages specified in requirements.txt
COPY --from=requirements_export requirements.txt /app
RUN pip install -r requirements.txt --no-cache-dir

COPY . /app

# For when run as nobody in environments on AWS
RUN chown -R nobody:nogroup /app
