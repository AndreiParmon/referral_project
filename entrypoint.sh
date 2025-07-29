#!/bin/bash
set -e

echo "🔍 Проверяем доступность PostgreSQL..."

until pg_isready -h "$DB_HOST" -p 5432 -U "$DB_USER"; do
  echo "⏳ База данных недоступна, ждём..."
  sleep 1
done

echo "✅ База данных доступна"

echo "🔄 Проверяем неприменённые миграции..."
if ! python manage.py migrate --check; then
  echo "📦 Применяем миграции..."
  python manage.py migrate
else
  echo "🟢 Миграции уже применены"
fi

echo "🚀 Запуск Django"
exec "$@"