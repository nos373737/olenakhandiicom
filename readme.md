# Olena Khandii Website

Personal Django website for an English teacher. The site is designed to work as a public profile, blog, service catalogue, reviews page, and a future base for monetisation through groups, digital products, newsletters, or paid learning content.

## Stack

- Python / Django
- SQLite for local development
- Bootstrap 4 vendor assets plus custom CSS
- Gunicorn for production-style serving
- WhiteNoise for static files

## Local Setup

The Makefile is the source of truth for day-to-day commands.

```bash
make install
make migrate
make run-dev
```

Open the site at:

```text
http://127.0.0.1:8000/
```

Open the Django admin at:

```text
http://127.0.0.1:8000/admin/
```

Create an admin user when needed:

```bash
venv/bin/python manage.py createsuperuser
```

## Makefile Commands

```bash
make install-venv
```

Creates the local `venv`.

```bash
make install-deps-in-venv
```

Installs Python dependencies into `venv`.

```bash
make install
```

Creates the virtual environment if needed and installs dependencies.

```bash
make migrate
```

Applies database migrations.

```bash
make collectstatic
```

Collects static assets for production-style serving.

```bash
make test
```

Runs the Django test suite.

```bash
make run-dev
```

Runs the Django development server on `0.0.0.0:8000`.

```bash
make run-webserver
```

Runs migrations, collects static files, and starts Gunicorn with `gunicorn_config.py`.

```bash
make run-webserver-bg
```

Starts Gunicorn in the background and writes output to `gunicorn.log`.

## Content Workflow

1. Create categories in Django admin.
2. Add blog posts with title, category, content, and image.
3. Use the public blog page to validate how posts appear.
4. Keep service, pricing, rules, and review pages updated as the business offer changes.

## Learning Request Form

The header button `Запит на навчання` opens `/contact`.

This page now contains:

- a B1+ diagnostic placement test description
- downloadable PDF test file
- downloadable MP3 listening file
- upload form for completed answers

Uploaded answers are attached to an email and sent to `DJANGO_TEACHER_EMAIL`.

Local development uses Django's console email backend by default. For production email delivery, configure SMTP in `/etc/olena-khandii.env`:

```bash
DJANGO_TEACHER_EMAIL=olenakhandii@gmail.com
DJANGO_DEFAULT_FROM_EMAIL=website@olenakhandii.com
DJANGO_EMAIL_HOST=smtp.example.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=your-smtp-user
DJANGO_EMAIL_HOST_PASSWORD=your-smtp-password
DJANGO_EMAIL_USE_TLS=True
```

Then restart the service:

```bash
sudo systemctl restart olena-khandii
```

## Application Logs

Production application events, request timing, and exception tracebacks are written to:

```text
/var/log/olenakhandii/website.log
```

Follow the log while reproducing a problem:

```bash
sudo tail -f /var/log/olenakhandii/website.log
```

For an existing server that was provisioned before application file logging was added, create the writable path once before deploying the updated application:

```bash
sudo install -d -o www-data -g www-data -m 0750 /var/log/olenakhandii
sudo touch /var/log/olenakhandii/website.log
sudo chown www-data:www-data /var/log/olenakhandii/website.log
sudo chmod 0640 /var/log/olenakhandii/website.log
sudo install -m 0644 /opt/website/deploy/olena-khandii.logrotate /etc/logrotate.d/olena-khandii
```

Contact submissions log milestones for validation, database persistence, attachment preparation, and SMTP delivery. Personal message contents, passwords, and uploaded file contents are not logged. Logs rotate daily and 14 compressed rotations are retained.

Local development logs to the console. The production path and log level can be overridden with `DJANGO_WEBSITE_LOG_PATH` and `DJANGO_LOG_LEVEL`.

## Frontend Direction

The current design is built around a personal teacher brand rather than a generic blog template:

- clear hero with Olena as the first-viewport signal
- direct paths to services, prices, blog, and real Instagram reviews
- modern editorial blog cards with image fallbacks
- placeholders that make future newsletter or paid content features straightforward

## Notes

- `db.sqlite3` is suitable for local development. Use a production database before serious monetisation.
- Move sensitive settings such as `SECRET_KEY` and `DEBUG` to environment variables before production hardening.
- Add real tests around post creation, comments, contact requests, and auth flows as the project grows.
