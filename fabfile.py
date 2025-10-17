from fabric import task

from fab.database import (
    # copy_database_to_sandbox,
    # copy_media_files,
    upload_database,
    create_database,
    download_database,
    do_terminate,
)
from fab.deployment import (
    deploy_django,
    deploy_django_fast,
    # start_background,
    # stop_background,
    # status_background,
    # maintenance as do_maintenance,
)
from fab.provision import (
    install_app as do_install_app,
    install_system_software as do_install_system_software,
    configure_firewall,
)
from fab.settings import get_connection, blue, green


# Start Shell
# ./venv/bin/python manage.py shell --settings=mysite.settings.live
# Download media from digital ocean
# rsync -a django@coombewoodltc.co.uk:cwltc/media cwltc
# Upload media to hetzner
# rsync -a --info=progress2 cwltc/media django@sandbox.iskt.co.uk:sandbox


@task
def deploy(c, host="", sandbox=False, live=False, fast=False):
    """Full deployment to live or sandbox site"""
    c = get_connection(host=host, sandbox=sandbox, live=live)
    if fast:
        deploy_django_fast(c)
    else:
        deploy_django(c)


@task
def create(c, host="", sandbox=False, dev=False, live=False, win=False):
    c = get_connection(host=host, sandbox=sandbox, dev=dev, live=live)
    c.win = win
    create_database(c)


@task
def download(c, sandbox=False, dev=False, live=True):
    """Download database. Default is from live site"""
    c = get_connection(host="", sandbox=sandbox, dev=dev, live=live)
    download_database(c)


@task
def upload(c, host="", sandbox=False, dev=False, live=False, win=False, file=""):
    """Upload database No default"""
    c = get_connection(host="", sandbox=sandbox, dev=dev, live=live)
    c.win = win
    if file:
        upload_database(c, backup_file=file)
    else:
        upload_database(c)


# @task
# def copy_db(c):
#     """Copy database from live to sandbox"""
#     c = get_connection(live=True)
#     copy_database_to_sandbox(c)
#
#
# @task
# def upload_media(c, host="", sandbox=False, live=False):
#     c = get_connection(host="", sandbox=sandbox, live=live)
#     source = "~/cwltc/media"
#     target = f"{c.user}@{c.host}:{c.app}"
#     cmd = f"rsync -a --info=progress2 {source} {target}"
#     print(blue(f"Executing {cmd}"))
#     c.local(cmd)
#     print(green("End rsync"))
#


@task
def download_media(c, sandbox=False, live=False):
    c = get_connection(host="", sandbox=sandbox, live=live)
    source = f"{c.user}@{c.host}:{c.app}/media"
    target = "."
    cmd = f"rsync -a --info=progress2 {source} {target}"
    print(blue(f"Executing {cmd}"))
    c.local(cmd)
    print(green("End rsync"))


# @task
# def copy_media(c):
#     """Copy media files from live to sandbox"""
#     c = get_connection(live=True)
#     copy_media_files(c)
#
#
# @task
# def install_system(c, host="", sandbox=False, dev=False, live=False):
#     """Install system software on a new server"""
#     c = get_connection(host=host, sandbox=True, branch="master")
#     if c.sandbox:
#         c.server = "sandbox.coombewoodltc.com"
#     elif c.live and "coombewood" in host:
#         c.server = "www.coombewoodltc.co.uk"
#     configure_firewall
#     do_install_system_software(c)
#     pass
#
#
# @task
# def install_app(c, host="", sandbox=False, dev=False, live=False):
#     c = get_connection(host=host, sandbox=sandbox, live=live)
#     if c.sandbox:
#         c.server = "sandbox.coombewoodltc.com"
#     elif c.live and "coombewood" in host:
#         c.server = "www.coombewoodltc.co.uk"
#     do_install_app(c)
#
#
# @task
# def start_bg(c, host="", sandbox=False, dev=False, live=False):
#     c = get_connection(host=host, sandbox=sandbox, dev=dev, live=live)
#     start_background(c)
#
#
# @task
# def stop_bg(c, host="", sandbox=False, dev=False, live=False):
#     c = get_connection(host=host, sandbox=sandbox, dev=dev, live=live)
#     stop_background(c)
#
#
# @task
# def status_bg(c, host="", sandbox=False, live=False):
#     c = get_connection(host=host, sandbox=sandbox, dev=False, live=live)
#     status_background(c)
#


@task
def terminate(c, host="", sandbox=False, dev=False, live=False, win=False):
    """Terminate active database connections"""
    c = get_connection(host=host, sandbox=sandbox, dev=dev, live=live)
    c.win = win
    do_terminate(c)


#
# @task
# def maintenance(c, host="", sandbox=False, dev=False, live=False, show=False):
#     c = get_connection(host=host, sandbox=sandbox, dev=False, live=live)
#     do_maintenance(c, show=show)
