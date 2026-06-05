FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=mysite.settings.live \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create user first so subsequent files are owned correctly — avoids a slow chown -R at the end
RUN useradd --create-home --system appuser

WORKDIR /app
RUN chown appuser /app
USER appuser

# Install dependencies before copying app code so this layer is cached
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-cache

# Copy application code
COPY --chown=appuser:appuser app/ .

# Collect static files at build time.
# Dummy env vars satisfy django-environ; no real secrets end up in the image.
RUN touch .env && \
    SECRET_KEY=build-only \
    DATABASE_URL=sqlite:///tmp/build.db \
    SENTRY=https://0@sentry.io/0 \
    SITEMAIL=x \
    CAPTCHA_SECRET=x \
    CAPTCHA_SITE=x \
    HCAPTCHA_SECRET=x \
    HCAPTCHA_SITE=x \
    python manage.py collectstatic --noinput && \
    rm .env

EXPOSE 8000
CMD ["gunicorn", "mysite.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120"]