from fab.settings import token_repo  # MAINT


def pull(c):
    c.run(f"cd {c.folder} && git pull {token_repo()} {c.branch}")


def collect_static(c):
    c.run(
        f"cd {c.folder} && {c.venv}/python manage.py collectstatic --noinput --settings={c.django_settings}"
    )


def install_requirements(c):
    if c.uv:
        c.run(f"cd {c.folder} && /home/django/.local/bin/uv sync --no-dev --locked")
    else:
        c.run(f"cd {c.folder} && {c.venv}/pip install -r requirements.txt")


def migrate(c):
    c.run(
        f"cd {c.folder} && {c.venv}/python manage.py migrate --noinput --settings={c.django_settings}"
    )


def put_env(c):
    source = ".env"
    target = f"{c.folder}/.env"
    c.put(source, target)


def clear_sessions(c):
    c.run(
        f"cd {c.folder} && {c.venv}/python manage.py clearsessions --settings={c.django_settings}"
    )


def stop_all(c):
    # stop_background(c)
    stop_gunicorn(c)


def start_all(c):
    start_gunicorn(c)
    # start_background(c)


# def stop_background(c):
#     for command in c.command_list:
#         if command[1]:
#             c.sudo(f"user={c.user}, supervisorctl stop {command[0]}", hide="stderr")
#
#
# def start_background(c):
#     for command in c.command_list:
#         if command[1]:
#             c.sudo(f"user={c.user}, supervisorctl start {command[0]}", hide="stderr")


# def status_background(c):
#     c.sudo(f"user={c.user}, supervisorctl status", hide="stderr")


def stop_gunicorn(c):
    c.sudo(f"systemctl stop gunicorn-{c.app}.socket", hide="stderr")
    c.sudo(f"systemctl stop gunicorn-{c.app}.service", hide="stderr")


def start_gunicorn(c):
    c.sudo(f"systemctl start gunicorn-{c.app}.service", hide="stderr")
    c.sudo(f"systemctl start gunicorn-{c.app}.socket", hide="stderr")


def deploy_django_fast(c):
    stop_all(c)
    pull(c)
    put_env(c)
    start_all(c)


def deploy_django(c):
    # maintenance(c, show=True)
    stop_all(c)
    pull(c)
    put_env(c)
    install_requirements(c)
    collect_static(c)
    migrate(c)
    clear_sessions(c)
    start_all(c)
    # maintenance(c, show=False)


# def maintenance(c, show=True):
#     if show:
#         c.run(f"cp {c.folder}/deployment/{MAINT} {c.folder}/{MAINT}")
#     else:
#         c.run(f"rm -f {c.folder}/{MAINT}")
