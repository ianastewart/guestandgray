import os
import time
from fab.settings import (
    BACKUP_FILE,
    BACKUP_FOLDER,
    blue,
    green,
)
from invoke import run
from invoke.context import Context, Config


# If upgrading to a later database version, remember to change the path
# so that latest version of pg_dump and restore are used


# Note can set passwd for default postgres user using: sudo passwd postgres


def create_database(c):
    """Creates role and database"""
    print(blue(f"Start create database {c.db_name}"))
    read_users = (
        f"psql -c \"SELECT rolname FROM pg_roles WHERE rolname = '{c.db_user}';\""
    )
    create_user = (
        f"psql -c \"CREATE USER {c.db_user} WITH CREATEDB PASSWORD '{c.db_pw}'\""
    )

    if c.win:
        cmd = f'CREATE USER {c.db_user} WITH CREATEDB PASSWORD "{c.db_pw}"'
        os.system(f'psql -U postgres -p {c.db_port} -c "{cmd}"')
        cmd = f"CREATE DATABASE {c.db_name} WITH OWNER {c.db_user}"
        os.system(f'psql -U postgres -p {c.db_port} "{cmd}"')
    else:
        result = c.sudo(
            f"psql -c \"SELECT rolname FROM pg_roles WHERE rolname = '{c.db_user}';\"",
            user="postgres",
        )
        if c.db_user not in result.stdout:
            print(blue("Creating user"))
            c.sudo(
                "psql -c \"CREATE USER %s WITH CREATEDB PASSWORD '%s'\""
                % (c.db_user, c.db_pw),
                user="postgres",
            )
        result = c.sudo(
            'psql -c "SELECT datname FROM pg_database WHERE datistemplate = false;"',
            user="postgres",
        )
        if c.db_name in result.stdout:
            print(blue(f"Dropping existing database {c.db_name}"))
            c.sudo(f"dropdb {c.db_name}", user="postgres")
        c.sudo(
            f'psql -c "CREATE DATABASE {c.db_name} WITH OWNER {c.db_user}"',
            user="postgres",
        )
    print(green(f"End create database {c.db_name}"))


def upload_database(c, backup_file=BACKUP_FILE):
    do_terminate(c)
    print(blue(f"Start upload database {c.db_name} to {c.folder} on {c.site}"))
    if c.win:
        os.system(f'psql -U postgres -p {c.db_port} -c "DROP DATABASE {c.db_name}')
        os.system(
            f'psql -U postgres -p {c.db_port} -c "CREATE DATABASE {c.db_name} WITH OWNER django"'
        )
        os.system(
            f"pg_restore -U postgres -p {c.db_port} -d {c.db_name} {BACKUP_FOLDER}/{backup_file}"
        )
        # print(green("Database uploaded"))
        # os.system(
        #     "python manage.py wagtail_site localhost 8000 --settings=mysite.settings.dev"
        # )
    elif c.dev:
        # These commands assume default user (ian) is a postgres superuser
        # os.system(f'psql -U postgres -p {c.db_port} -c "DROP DATABASE {c.db_name}')
        run(f"PGPASSWORD=ian dropdb -U ian -h localhost -p 5432 {c.db_name}")
        run(
            f"PGPASSWORD=ian createdb -U ian -O django -h localhost -p 5432 {c.db_name}"
        )
        run(
            f"PGPASSWORD=ian pg_restore -U ian -h localhost -p 5432 -d {c.db_name} {BACKUP_FOLDER}/{BACKUP_FILE}"
        )
    else:
        c.run(f"cd {c.folder} && mkdir -p {BACKUP_FOLDER}")
        c.put(
            f"{BACKUP_FOLDER}/{BACKUP_FILE}",
            f"{c.folder}/{BACKUP_FOLDER}/{BACKUP_FILE}",
        )
        create_database(c)
        print(blue("Start pg_restore"))
        c.run(f"pg_restore -d {c.db_name} {c.folder}/{BACKUP_FOLDER}/{BACKUP_FILE}")
        print(green("End pg_restore"))
    print(green(f"End upload database {c.db_name}"))


def dump_db(c):
    print(blue(f"Start dump database {c.db_name}"))
    c.run(f"mkdir -p {c.folder}/{BACKUP_FOLDER}")
    source_path = f"{c.folder}/{BACKUP_FOLDER}/{BACKUP_FILE}"
    c.run(f"pg_dump {c.db_name} -Fc -x >{source_path}")
    print(green(f"End dump database {c.db_name}"))
    return source_path


def download_database(c):
    print(blue(f"Start download database {c.db_name} from {c.site}"))
    local_path = f"{BACKUP_FOLDER}/{BACKUP_FILE}"
    if os.path.exists(local_path):
        # rename the backup file to include the modification date
        # but overwrite any backups already made today
        t = time.localtime(os.path.getmtime(local_path))
        f = BACKUP_FILE.split(".")
        new_path = f"{BACKUP_FOLDER}/{f[0]}_{t.tm_year}-{t.tm_mon}-{t.tm_mday}.{f[1]}"
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(local_path, new_path)

    source_path = dump_db(c)
    c.get(source_path, local_path)
    print(green(f"End download database {c.db_name}"))


def create_user(c):
    c.sudo(f"create user {c.db_user}", user="postgres")


def grant_privileges(c):
    if c.win:
        os.system(
            f'psql -U postgres -p {c.db_port} -c "GRANT ALL PRIVILEGES ON DATABASE {c.db_name} TO {c.db_user};"'
        )

    else:
        c.sudo(
            f'psql -d {c.db} -c "GRANT ALL PRIVILEGES ON DATABASE {c.db} TO {c.db_user};"',
            user="postgres",
        )
    c.sudo(
        f'psql -d {c.db} -c "GRANT ALL ON ALL TABLES IN SCHEMA public to {c.db_user};"',
        user="postgres",
    ),
    c.sudo(
        f'psql -d {c.db} -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public to {c.db_user};"',
        user="postgres",
    ),
    c.sudo(
        f'psql -d {c.db} -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public to {c.db_user};"',
        user="postgres",
    ),


# def copy_media_files(c):
#     source_app = "cwltc"
#     target_app = "sandbox"
#     print(blue(f"Start copy media from {source_app} to {target_app} on {c.site}"))
#     c.run(f"cp -r /home/django/{source_app}/media /home/django/{target_app}")
#     print(green("Media copied"))
#
#
# def copy_database_to_sandbox(c):
#     """Copy admin database to sandbox on remote server"""
#     source_path = dump_db(c)
#     c.db_name = "sandbox"
#     create_database(c)
#     c.sudo(f"pg_restore -d {c.db_name} {source_path}", user="postgres")
#     set_wagtail_site(c, "sandbox.coombewoodltc.com", "80")
#
#
# def set_wagtail_site(c):
#     if c.dev:
#         run(
#             f"{c.venv}/python manage.py wagtail_site localhost 8000 --settings={c.django_settings}"
#         )
#     else:
#         hostname = (
#             "sandbox.coombewoodltc.com" if c.sandbox else "www.coombewoodltc.co.uk"
#         )
#         c.run(
#             f"cd {c.folder} && {c.venv}/python manage.py wagtail_site {hostname} 80 --settings={c.django_settings}"
#         )


def do_terminate(c):
    if c.dev:
        ctx = Context(config=Config(overrides={"sudo": {"password": "ian"}}))
    cmd = f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity \
        WHERE pg_stat_activity.datname = '{c.db_name}' AND pid <> pg_backend_pid()"
    if c.win:
        os.system(f'psql -U postgres -p {c.db_port} -c "{cmd}"')
    elif c.dev:
        ctx = Context(config=Config(overrides={"sudo": {"password": "ian"}}))
        ctx.sudo(f'-u postgres psql -d {c.db_name} -c "{cmd}"')
    else:
        c.sudo(f'-u postgres psql -d {c.db_name} -c "{cmd}"')
