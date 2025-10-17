import re
from fabric import Connection, Config

# from fabric.api import cd, env, run
HOST = "213.171.212.38"
REPO = "github.com/ianastewart/guestandgray"

BACKUP_FOLDER = "database_backup"
BACKUP_FILE = "gray.dump"
MEDIA_FILE = "media.zip"
HOST_FOLDER = "gray"
# LOCAL_PATH = "C:/Users/is/PycharmProjects"
# LOCAL_PATH = "ls"
# LOCAL_DEV_FOLDER = LOCAL_PATH + "/cwltc"
# LOCAL_BACKUP_FOLDER = LOCAL_PATH + "/DatabaseBackups"
# COMMAND_LIST = [("db_worker", True), ("overnight", False)]
# MAINT = "maintenance.html"
# SANDBOX_TASK_LIST = ["sandbox", "db_worker_sandbox"]


def get_connection(
    host="",
    sandbox=False,
    dev=False,
    live=False,
    branch="master",
):
    if not (sandbox or dev or live):
        raise Exception(
            red("Connection error. You must specify one of --sandbox, --dev or --live")
        )
    if (sandbox and live) or (dev and live) or (sandbox and dev):
        raise Exception(
            red(
                "Connection error. You must specify only one of --sandbox, --dev or --live"
            )
        )
    if host == "":
        if live:
            host = HOST
            server = HOST
        elif sandbox:
            host = None
            server = None
        else:
            host = "localhost:8000"
            server = host
    password = read_password()
    config = Config(overrides={"sudo": {"password": password}})
    c = Connection(
        host, user="django", connect_kwargs={"password": password}, config=config
    )
    c.db_user, c.db_pw, c.db_port, c.db_name, c.app = get_db_settings(sandbox, dev)
    c.sandbox = sandbox
    c.dev = dev
    c.live = live
    c.site, c.folder = site_and_folder(c)
    c.workers = 2 if sandbox else 6
    c.branch = branch
    c.server = server
    c.django_settings = f"mysite.settings.{c.site}"
    # if no /venv folder this is hertzner server with uv and .venv
    c.venv = ".venv/bin"
    c.uv = True
    if not c.dev:
        result = c.run(
            f"test -d {c.folder}/venv && echo 'exists' || echo 'missing'", hide=True
        )
        if "exists" in result.stdout:
            c.venv = "/venv/bin"  # digital ocean server with pip
            c.uv = False
        # c.command_list = COMMAND_LIST
    return c


def site_and_folder(c):
    if c.dev:
        return "dev", ""
    elif c.sandbox:
        return "sandbox", "sandbox"
    elif c.live:
        return "live", HOST_FOLDER
    raise Exception(red("Connection has no system flags"))


class Clr:
    PURPLE = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"


def red(string):
    return Clr.RED + string + Clr.END


def blue(string):
    return Clr.BLUE + string + Clr.END


def green(string):
    return Clr.GREEN + string + Clr.END


def get_db_settings(sandbox=False, dev=False):
    dot_env = read_env()
    if sandbox:
        db_url = "DATABASE_URL_SANDBOX"
    elif dev:
        db_url = "DATABASE_URL_DEV"
    else:
        db_url = "DATABASE_URL"
    app = "sandbox" if sandbox else "gray"
    user, pw, port, db = parse_db_settings(dot_env[db_url])
    return user, pw, port, db, app


def parse_db_settings(value):
    parts = value.split(":")
    user = parts[1][2:]
    pw = parts[2].split("@")[0]
    port = parts[3].split("/")[0]
    db = parts[3].split("/")[1]
    print(f"User: {user},", f"Password: {pw},", f"Port: {port},", f"Database: {db}")
    return user, pw, port, db


def read_env():
    # read our .env file into a dictionary
    envre = re.compile(r"""^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$""")
    result = {}
    with open(".env") as ins:
        for line in ins:
            match = envre.match(line)
            if match is not None:
                result[match.group(1)] = match.group(2)
    return result


def read_password():
    return read_env()["DJANGO"]


def token_repo():
    token = read_env()["REPO_TOKEN"]
    return f"https://{token}@{REPO}"
