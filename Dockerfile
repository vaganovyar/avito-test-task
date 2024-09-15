FROM sunpeek/poetry:py3.11-slim

COPY . .
RUN poetry install

EXPOSE 8080

CMD poetry run python3 -m tenders
