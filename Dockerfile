FROM python:3.10-alpine as python
WORKDIR /app

FROM python as poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN apk add --no-cache gcc libc-dev \
    && pip3 install poetry
COPY . ./
RUN poetry install --no-interaction --no-ansi

FROM python as runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=poetry /app /app
ENTRYPOINT python3 phigros_bot/main.py $0 $@