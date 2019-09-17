import re
import os
import time
from fabric.contrib.files import exists
from fabric.colors import red, green, yellow, cyan
from fabric.api import hosts, cd, env, run, sudo, put, get
from fabric.context_managers import hide

from deployment.database_helper import (
    create_database,
    upload_database,
    download_database,
    upload_dev_db,
    create_user,
    grant_priviliges,
    upload_media,
    download_media,
    upload_media_dev,
    dump_dev_db,
)

# from fabric.network import ssh
# ssh.util.log_to_file("paramiko.log", 10)

REPO_URL = "https://github.com/ianastewart/guestandgray"
BACKUP_FOLDER = "GuestAndGray/Backup"
# LOCAL_DEV_FOLDER = "D:/Django/admin/"
BACKUP_FOLDER = "database_backup"
BACKUP_FILE = "gray.dump"
MEDIA_FILE = "media.zip"


def _local_path():
    if os.path.exists("D:/Django"):
        return "D:/Django"
    else:
        return "C:/Users/is"


def _local_dev_folder():
    if os.path.exists("D:/Django"):
        return "D:/Django/GuestAndGray"
    else:
        return "C:/Users/is/PycharmProjects/GuestAndGray"


# @hosts("46.101.88.176")
@hosts("77.68.81.128")
def provision():
    """
    Provision a new site with live data. Does everything except install certificate.
    Before running: Copy deployment.first_setup.sh to root folder using filezilla and make it executable
    Log in as root and execute it

    """
    dot_env = _read_env()
    env.user = "django"
    env.password = dot_env["DJANGO"]
    _install_system_software()
    _install_app()


# @hosts("46.101.88.176")
@hosts("77.68.81.128")
def install_app(app="gray", settings="prod", branch="master"):
    """ Install application, defaults to sandbox """
    dot_env = _read_env()
    env.user = "django"
    env.password = dot_env["DJANGO"]
    _install_app(app, settings, branch)


# @hosts("gray.iskt.co.uk")
@hosts("77.68.81.128")
def download():
    """ Download database and media from live site"""
    env.user = "django"
    env.password = _read_env()["DJANGO"]
    app = "gray"
    db = "gray"
    download_database(_local_dev_folder(), app, db)
    download_media(_local_dev_folder(), app)


@hosts("gray.iskt.co.uk")
def upload_db():
    """ Upload database to live site"""
    env.user = "django"
    env.password = _read_env()["DJANGO"]
    dbuser, pw, db = _parse_db_settings()
    upload_database(_local_dev_folder(), app="gray", dbuser=dbuser, pw=pw, db=db)


def upload_dev():
    """ Replace database and media on dev system"""
    upload_dev_db(_local_dev_folder(), "gray")
    upload_media_dev(_local_dev_folder())


def dump_dev():
    dbuser, pw, db = _parse_db_settings()
    dump_dev_db(_local_dev_folder(), dbuser, pw, db)


@hosts("77.68.81.128")
def create_dbuser():
    """ Create django as dbuser """
    dbuser, pw, db = _parse_db_settings()
    dbuser = "django"
    create_user(dbuser, pw)
    grant_priviliges(dbuser, db)


@hosts("django.iskt.co.uk")
def status():
    """ Status of live site """
    with hide("output"):
        env.user = "django"
        env.password = _read_env()["DJANGO"]
        result1 = sudo(f"supervisorctl status")
        result2 = sudo("free")
        print(result1)
        print(result2)


@hosts("gray.iskt.co.uk")
def manage(app, command):
    """ Example fab manage:sandbox,migrate """
    env.user = "django"
    env.password = _read_env()["DJANGO"]
    app = "gray"
    settings = "prod"
    site_folder = f"/home/django/{app}"
    prefix = f"./venv/bin/"
    django_settings = f"mysite.settings.{settings}"
    with cd(site_folder):
        run(
            # f"{prefix}python manage.py {command} --noinput --settings={django_settings}"
            f"{prefix}python manage.py {command} --settings={django_settings}"
        )


# @hosts("gray.iskt.co.uk")
@hosts("77.68.81.128")
def deploy_live(command=False):
    """ Deploy application changes to live server """
    env.user = "django"
    env.password = _read_env()["DJANGO"]
    fast = True if command == "fast" else False
    _deploy_helper(
        "venv",
        app="gray",
        settings="prod",
        branch="master",
        collect_static=True,
        fast=fast,
    )


def _deploy_helper(
    venv, app, settings, branch, tasks=None, collect_static=True, fast=False
):
    if exists(f"/home/django/{app}"):
        # _maintenance(app, show=True)
        sudo(f"supervisorctl stop {tasks}")
        sudo(f"supervisorctl stop {app}")
    _deploy_django(venv, app, settings, branch, collect_static, fast)
    if tasks:
        sudo(f"supervisorctl start {tasks}")
    sudo(f"supervisorctl start {app}")
    # _maintenance(app, show=False)
    status()


def _install_system_software():
    print(yellow("Start install system software"))
    sudo("apt-get update")
    sudo("apt-get -y upgrade")
    _setup_firewall()
    sudo("apt-get -y install zip gzip tar")
    # install PostgresSQL & create user and database
    sudo("apt-get -y install build-essential libpq-dev python-dev")
    sudo("apt-get -y install postgresql postgresql-contrib")
    # install NGINX
    sudo("apt-get -y install nginx")
    # install pip and venv
    sudo("apt-get -y install python3-pip")
    sudo("apt-get -y install python3-venv")
    # install supervisor and start it
    sudo("apt-get -y install supervisor")
    sudo("systemctl enable supervisor")
    sudo("systemctl start supervisor")
    # install certbot from certbot maintained repository
    sudo("sudo add-apt-repository -y ppa:certbot/certbot")
    sudo("apt-get -y install python-certbot-nginx")
    # install git
    sudo("apt-get -y install git")
    print(green("End install system software"))


def _setup_firewall():
    print(yellow("Start setup firewall"))
    sudo("ufw enable")
    sudo("ufw allow OpenSSH")
    sudo("ufw allow 80")
    sudo("ufw allow 443")
    sudo("ufw allow from 82.19.142.238 to any port 5432 proto tcp")
    print(green("End setup firewall"))


def _create_venv(venv, app, repo=REPO_URL):
    # Make app folder, clone django repo and create a venv
    site_folder = f"/home/django/{app}"
    sudo(f"mkdir -p {site_folder}", user="django")
    if not exists(f"{site_folder}/.git"):
        sudo(f"git clone {repo} {site_folder}", user="django")
    sudo(f"python3 -m venv {site_folder}/{venv}", user="django")
    sudo(
        f"mkdir -p {site_folder}/logs && touch {site_folder}/logs/django.log",
        user="django",
    )


def _install_app(app="gray", settings="prod", branch="master"):
    """
    Upload a database and install application in virtual env,
    Install gunicorn and configure nginx to support it
    """
    venv = "venv"
    dbuser, pw, db = _parse_db_settings()
    # virtual environment
    _create_venv(venv, app)
    create_database(dbuser=dbuser, pw=pw, db=db)
    # _upload_database(app, user, pw, db)
    # _upload_media(app)
    _deploy_django(venv, app, settings, branch)
    _install_gunicorn(venv, app, settings)

    server = env.host
    _configure_nginx(app, server)
    sudo("supervisorctl reread")
    sudo("supervisorctl update")
    sudo("supervisorctl status")


def _deploy_django(venv, app, settings, branch, collect_static=True, fast=False):
    """ Update django app from repo, update requirements, collect static and migrate """
    print(yellow("Start deploy Django"))
    if venv:
        venv += "/"  # compatibility with old deployment
    site_folder = f"/home/django/{app}"
    prefix = f"./{venv}bin/"
    django_settings = f"mysite.settings.{settings}"
    with cd(site_folder):
        run("git fetch --all")
        run(f"git reset --hard origin/{branch}")
        put(".env", site_folder + "/.env")
        if fast:
            print(green("End fast deploy Django"))
            return
        run(f"{prefix}pip install wheel")
        run(f"{prefix}pip install -r requirements.txt")
        if collect_static:
            run(
                f"{prefix}python manage.py collectstatic --noinput --settings={django_settings}"
            )
        run(f"{prefix}python manage.py migrate --noinput --settings={django_settings}")
        run(f"{prefix}python manage.py clearsessions --settings={django_settings}")
    print(green("End deploy Django"))


def _install_gunicorn(venv, app, settings):
    # install gunicorn in virtual environment and configure it by modifying gunicorn_start template
    print(yellow("Start install Gunicorn"))
    site_folder = f"/home/django/{app}"
    prefix = f"./{venv}/bin/"

    with cd(site_folder):
        run(f"{prefix}pip install gunicorn")
        template = "./deployment/gunicorn_start"
        output = f"{prefix}gunicorn_start"
        run(
            f"sed -e 's/XXapp/{app}/; s/XXsettings/{settings}/ ;s/XXvenv/{venv}/' {template} > {output}"
        )
        run(f"chmod u+x {output}")
        # directory for the unix socket file
        run("mkdir -p run")
        run("mkdir -p logs && > logs/gunicorn-error.log")
        # configure supervisor for gunicorn
        template = "./deployment/gunicorn.conf"
        output = f"/etc/supervisor/conf.d/{app}.conf"
        sudo(
            f">{output} && sed -e 's/XXapp/{app}/; s/XXvenv/{venv}/' {template} > {output}"
        )
    print(green("End install Gunicorn"))


@hosts("46.101.88.176")
def configure_nginx():
    dot_env = _read_env()
    env.user = "django"
    env.password = dot_env["DJANGO"]
    _configure_nginx("gray", "gray.iskt.co.uk")


def _configure_nginx(app, server):
    # create a site file for nginx based on a standard template
    print(yellow("Start configure Nginx"))
    template = f"/home/django/{app}/deployment/nginx_site"
    output = f"/etc/nginx/sites-available/{app}"
    enabled = "/etc/nginx/sites-enabled/"
    if exists(output, use_sudo=True):
        sudo(f"rm {output}")
    print(cyan(f"Creating new nginx config for {app}"))
    sudo(f"sed -e 's/XXapp/{app}/; s/XXserver/{server}/' {template} > {output}")
    sudo(f"rm -f {enabled}{app}")
    sudo(f"ln -s {output} {enabled}{app}")
    # sudo(f"rm -f /etc/nginx/sites-enabled/default")
    sudo("nginx -t")
    sudo("service nginx restart")
    print(green(f"End configure Nginx"))


def _parse_db_settings():

    dot_env = _read_env()
    db_url = "DATABASE_URL"
    parts = dot_env[db_url].split(":")
    dbuser = parts[1][2:]
    pw = parts[2].split("@")[0]
    db = parts[3].split("/")[1]
    return dbuser, pw, db


def _read_env():
    # read our .env file into a dictionary
    envre = re.compile(r"""^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$""")
    result = {}
    with open(".env") as ins:
        for line in ins:
            match = envre.match(line)
            if match is not None:
                result[match.group(1)] = match.group(2)
    return result
