#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Seed initial data (admin user, roles)
echo "Seeding database..."
python -m app.db.seed

# Start the application
echo "Starting application..."
exec "$@"
