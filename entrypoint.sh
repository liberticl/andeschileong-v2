#!/bin/bash
set -e

# Cleanup function: delete generated .md files on container stop
cleanup() {
    echo "Cleaning up generated .md files..."
    find /andeschileong/hugo_site/content/actividades -name '*.md' ! -name '_index.md' -delete 2>/dev/null || true
    find /andeschileong/hugo_site/content/noticias -name '*.md' -delete 2>/dev/null || true
    find /andeschileong/hugo_site/content/estudios -name '*.md' ! -name '_index.md' -delete 2>/dev/null || true
    echo "Cleanup done."
}

# Trap SIGTERM and SIGINT to run cleanup
trap cleanup SIGTERM SIGINT

# Sync Hugo content from DB
python manage.py sync_hugo

# Start nginx
service nginx start

# Start gunicorn
exec gunicorn --workers 3 andeschileong.wsgi:application --bind 0.0.0.0:8000 --log-level debug &
GUNICORN_PID=$!

# Wait for gunicorn (this keeps the container running)
wait $GUNICORN_PID

# Run cleanup on exit
cleanup
