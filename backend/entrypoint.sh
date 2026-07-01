#!/bin/sh
set -e

# Fix volume ownership when running as root, then drop to appuser.
if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser /app/media /app/staticfiles 2>/dev/null || true
    exec su -s /bin/sh appuser -c "exec $0"
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

exec daphne -b 0.0.0.0 -p 8000 --access-log - chat_app_django.asgi:application
