# Fabric2 support code to provision a new site
# NB if moving to a new domain set ALLOWED HOSTS accordingly

from fab.settings import green, blue
from fab.deployment import pull, put_env
from fab.database import upload_database
from fab.deployment import collect_static, migrate, start_all


def upgrade(c):
    c.sudo("apt-get update")
    c.sudo("apt-get -y upgrade")


def configure_firewall(c):
    c.sudo(
        "ufw enable && ufw allow OpenSSH && ufw allow 80 && ufw allow 443",
        hide="stderr",
    )
    c.sudo(
        "sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config",
        hide="stderr",
    )
    c.sudo("service ssh restart", hide="stderr")


def install_system_software(c):
    print(blue("Start install system software"))
    upgrade(c)
    c.sudo('timedatectl set-timezone "Europe/London"')
    # essential tools
    c.sudo(
        "apt-get -y install zip gzip tar build-essential libpq-dev python3-dev nginx supervisor"
    )
    c.sudo("systemctl enable supervisor")
    c.sudo("systemctl start supervisor")
    # install postresql and enable to start on boot
    c.sudo("apt-get -y install postgresql postgresql-contrib")
    c.sudo("systemctl start postgresql")
    # install uv in /home/django/.local/bin
    c.sudo("curl -LsSf https://astral.sh/uv/install.sh | sh")
    c.sudo("source $HOME/.local/bin/env")
    # install pip and venv
    # c.sudo("apt-get -y install python3-pip")
    # c.sudo("apt-get -y install python3-venv")
    # Stuff for playwright
    c.sudo(
        "apt-get -y install libx11-xcb1 libxcursor1 libgtk-3-0t64 libpangocairo-1.0-0 libcairo-gobject2 libgdk-pixbuf-2.0-0"
    )
    print(green("End install system software"))


def install_app(c):
    """
    Upload a database and install application in virtual env,
    Install gunicorn and configure nginx to support it
    """
    c.run(f"mkdir -p {c.app} {c.app}/logs && touch {c.app}/logs/django.log")
    c.run(f"cd {c.app} && git init")
    # remove any untracked files fleft from earlier runs
    c.run(f"cd {c.app} && git clean -f")
    pull(c)
    put_env(c)
    c.run(f"cd {c.app} && /home/django/.local/bin/uv sync --no-dev")
    upload_database(c)
    collect_static(c)
    migrate(c)
    configure_gunicorn(c)
    # install_tasks(c)
    start_all(c)
    configure_nginx(c)
    c.sudo("supervisorctl reread")
    c.sudo("supervisorctl update")
    c.sudo("supervisorctl status")


def install_playwright(c):
    c.run(f"cd {c.folder} && {c.venv}/playwright install")


def configure_gunicorn(c):
    """
    Gunicorn is installed as a service and is connected to a socket which triggers the start of gunicorn
    Gunicorn is managed by supervisorctl
    https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu
    To test basic gunicorn is working before configuration (with firewall allowing 8000), inside the venv type:
        gunicorn --bind 0.0.0.0:8000 mysite.wsgi --env DJANGO_SETTINGS_MODULE=mysite.settings.sandbox
    """
    print(blue("Start config Gunicorn"))
    # Create socket file.
    # Using sudo(sed...) to output to /etc/systemd/system had permission problems so we go via a temp file
    template = f"{c.app}/deployment/gunicorn.socket"
    temp = f"{c.app}/deployment/gunicorn-{c.app}.socket"
    output = f"/etc/systemd/system/gunicorn-{c.app}.socket"
    c.run(f"sed -e 's|XXapp|{c.app}|;' {template} > {temp}")
    c.sudo(f"mv {temp} {output}")
    # Same for the service file
    template = f"{c.app}/deployment/gunicorn.service"
    temp = f"{c.app}/deployment/gunicorn-{c.app}.service"
    output = f"/etc/systemd/system/gunicorn-{c.app}.service"
    c.run(
        f"sed -e 's|XXapp|{c.app}|; s|XXsettings|{c.django_settings}|; s|XXvenv|{c.venv}|; s|XXworkers|{c.workers}|;' {template} > {temp}"
    )
    c.sudo(f"mv {temp} {output}")
    # Create logs folder with empty logfile
    c.run(f"cd {c.app} && mkdir -p logs && > logs/gunicorn-error.log")
    # Start and enable it
    c.sudo("systemctl daemon-reload")
    c.sudo(f"systemctl start gunicorn-{c.app}.socket")
    c.sudo(f"systemctl enable gunicorn-{c.app}.socket")
    print(green("End config Gunicorn"))


def configure_nginx(c):
    # create a site file for nginx based on a standard template
    print(blue("Start configure Nginx"))
    template = f"/home/django/{c.app}/deployment/nginx-site"
    temp = f"{c.app}/deployment/nginx-{c.app}"
    output = f"/etc/nginx/sites-available/{c.app}"
    c.run(f"sed -e 's/XXapp/{c.app}/; s/XXserver/{c.server}/' {template} > {temp}")
    c.sudo(f"mv {temp} {output}")
    c.sudo(f"rm -f /etc/nginx/sites-enabled/{c.app}")
    c.sudo(f"ln -d {output} /etc/nginx/sites-enabled/{c.app}")
    c.sudo("rm -f /etc/nginx/sites-enabled/default")
    c.sudo("nginx -t")
    # nginx nees read and exec access to the django directory
    c.run("chmod 755 /home/django")
    c.sudo("service nginx restart")
    print(green("End configure Nginx"))


# def install_tasks(c):
#     # install script to start django-tasks and configure in supervisord
#     print(blue("Start install tasks"))
#     for command in COMMAND_LIST:
#         create_command(c, command[0], supervised=command[1])
#     c.sudo("supervisorctl reread")
#     c.sudo("supervisorctl update")
#     print(green("End install tasks"))


def create_command(c, command, supervised=False):
    # Create a shell program to start a python management command
    # and an optional .conf entry for supervisor to start it
    template = f"{c.app}/deployment/command.sh"
    output = f"{c.app}/{command}.sh"
    c.run(
        f"sed -e 's|XXapp|{c.app}|; s|XXvenv|{c.venv}|; s|XXsettings|{c.django_settings}|; s|XXcommand|{command}|' {template} > {output}"
    )
    c.run(f"chmod u+x {output}")
    if supervised:
        # conf creation goes via temp file
        template = f"{c.app}/deployment/supervisor.conf"
        temp = f"{command}.conf"
        output = f"/etc/supervisor/conf.d/{command}.conf"
        c.run(f"sed -e 's|XXapp|{c.app}|; s|XXprog|{command}|' {template} > {temp}")
        c.sudo(f"mv {temp} {output}")
