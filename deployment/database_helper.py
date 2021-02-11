# Database helper for fab file
import os
import subprocess
import time

from fabric.api import cd, get, put, run, sudo
from fabric.colors import cyan, green, yellow

LOCAL_BACKUP_FOLDER = "Backup"
BACKUP_FOLDER = "database_backup"
BACKUP_FILE = "gray.dump"
MEDIA_FILE = "media.zip"


def _create_database(dbuser, pw, db):
    """Creates role and database"""
    print(yellow(f"Start create database {db}"))
    db_users = sudo(
        "psql -c \"SELECT rolname FROM pg_roles WHERE rolname = '%s';\"" % (dbuser),
        user="postgres",
    )
    if not dbuser in db_users:
        sudo(
            "psql -c \"CREATE USER %s WITH CREATEDB PASSWORD '%s'\"" % (dbuser, pw),
            user="postgres",
        )
    databases = sudo(
        'psql -c "SELECT datname FROM pg_database WHERE datistemplate = false;"',
        user="postgres",
    )
    if db in databases:
        print(cyan(f"Dropping existing database {db}"))
        sudo(f"dropdb {db}", user="postgres")
    sudo('psql -c "CREATE DATABASE %s WITH OWNER %s"' % (db, dbuser), user="postgres")
    _grant_priviliges(dbuser, db)
    print(green(f"End create database {db}"))


def _create_user(dbuser, pw):
    db_users = sudo(
        "psql -c \"SELECT rolname FROM pg_roles WHERE rolname = '%s';\"" % (dbuser),
        user="postgres",
    )
    if not dbuser in db_users:
        sudo(
            "psql -c \"CREATE USER %s WITH CREATEDB PASSWORD '%s'\"" % (dbuser, pw),
            user="postgres",
        )
    print(green(f"User {dbuser} created"))


def _grant_priviliges(dbuser, db):
    sudo(
        f'psql -d {db} -c "GRANT ALL ON ALL TABLES IN SCHEMA public to {dbuser};"',
        f'psql -d {db} -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public to {dbuser};"',
        f'psql -d {db} -c "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public to {dbuser};"',
        user="postgres",
    )


def _download_database(local_dev_folder, app, db):
    print(yellow("Start download database"))
    site_folder = f"/home/django/{app}/"
    dbuser = "django"
    local_path = f"{local_dev_folder}/{BACKUP_FOLDER}/{BACKUP_FILE}"
    if os.path.exists(local_path):
        # rename the backup file to include the modification date
        # but overwrite any backups already made today
        t = time.localtime(os.path.getmtime(local_path))
        f = BACKUP_FILE.split(".")
        new_path = f"{local_dev_folder}/{BACKUP_FOLDER}/{f[0]}_{t.tm_year}-{t.tm_mon}-{t.tm_mday}.{f[1]}"
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(local_path, new_path)
    sudo(f"mkdir -p {site_folder}/{BACKUP_FOLDER}", user="django")
    source_path = f"{site_folder}/{BACKUP_FOLDER}/{BACKUP_FILE}"
    _grant_priviliges("django", "gray")
    sudo(f"pg_dump {db} -h localhost -Fc -x -U gray >{source_path}", user="django")
    get(source_path, local_path)
    print(green("End download database"))


def _upload_database(local_dev_folder, app, dbuser, pw, db):
    site_folder = f"/home/django/{app}"
    print(yellow(f"Start upload database {db} to {site_folder}"))
    with cd(site_folder):
        sudo(f"mkdir -p {BACKUP_FOLDER}", user="django")
        put(
            f"{local_dev_folder}/{BACKUP_FOLDER}/{BACKUP_FILE}",
            f"{BACKUP_FOLDER}/{BACKUP_FILE}",
        )
        _create_database(dbuser, pw, db)
        sudo(f"pg_restore -d {db} {BACKUP_FOLDER}/{BACKUP_FILE}", user="postgres")
    print(green(f"End upload database {db}"))


def _upload_dev_db(local_dev_folder, db):
    """ Replace database only dev system"""
    print(f"Replace dev database {db}")
    sql = f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity \
        WHERE pg_stat_activity.datname = '{db}' AND pid <> pg_backend_pid()"
    cmd = f'psql -U postgres -c "{sql}"'
    result = subprocess.check_output(cmd, shell=True)
    print(result)



    os.system(f'psql -U postgres -c "DROP DATABASE {db}"')
    os.system(f'psql -U postgres -c "CREATE DATABASE {db} WITH OWNER django"')
    os.system(
        f"pg_restore -U postgres -d {db} {local_dev_folder}/{BACKUP_FOLDER}/{BACKUP_FILE}"
    )
    venv = f"{local_dev_folder}/venv/Scripts/python.exe"
    os.system(
        f"{venv} manage.py wagtail_site localhost 8000 --settings=mysite.settings.dev"
    )


def _dump_dev_db(local_dev_folder, dbuser, pw, db):
    local_path = f"{local_dev_folder}/{BACKUP_FOLDER}/{BACKUP_FILE}"
    if os.path.exists(local_path):
        os.remove(local_path)
    os.system(f"SET PGPASSWORD={pw}")
    os.system(f"pg_dump -Fc -U {dbuser} --file={local_path} {db} ")
    print(f"Local database dumped to {local_path}")


def _download_media(local_dev_folder, app):
    # Only original_images
    print(yellow("Start download media"))
    site_folder = f"/home/django/{app}"
    with cd(site_folder):
        sudo(f"zip -r {MEDIA_FILE} media/original_images", user="django")
        get(MEDIA_FILE, f"{local_dev_folder}/{BACKUP_FOLDER}/{MEDIA_FILE}")
        sudo(f"rm {MEDIA_FILE}")
    print(green("End download media"))


def _upload_media(local_dev_folder, app):
    print(yellow("Start upload media"))
    site_folder = f"/home/django/{app}"
    sudo(f"mkdir -p {site_folder}", user="django")
    with cd(site_folder):
        run("rm -rf media")
        put(f"{local_dev_folder}/{BACKUP_FOLDER}/{MEDIA_FILE}", MEDIA_FILE)
        sudo(f"unzip {MEDIA_FILE}", user="django")
    print(green("End upload media"))


def _upload_media_dev(local_dev_folder):
    os.system(
        f'C:/"Program Files"/7-Zip/7z.exe x -y {local_dev_folder}/{BACKUP_FOLDER}/{MEDIA_FILE} -o{local_dev_folder}/"gray"'
    )
