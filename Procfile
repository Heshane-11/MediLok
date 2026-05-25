web: python manage.py collectstatic --noinput && gunicorn bitnbuild.wsgi --bind 0.0.0.0:$PORT
release: python manage.py migrate --noinput
