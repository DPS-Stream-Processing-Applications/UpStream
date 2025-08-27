FROM python:3.12 as builder

RUN pip install poetry==1.8.3

# Environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /mpc-scaler-flink

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:3.12-slim as runtime

ENV VIRTUAL_ENV=/mpc-scaler-flink/.venv \
    PATH="/mpc-scaler-flink/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY src /mpc-scaler-flink/src

ENV PYTHONPATH="/mpc-scaler-flink/src"

ENTRYPOINT ["python", "-m", "mpc_scaler_flink"]
