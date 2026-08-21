#!/bin/bash
# Usage: first_setup.sh <app-name>
APP_NAME="${1:?Usage: first_setup.sh <app-name>}"

adduser django
usermod -aG sudo django
mkdir /home/django/.ssh
cp ~/.ssh/authorized_keys /home/django/.ssh
chown -R django:django /home/django
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
service ssh restart

# nginx access/error logs live under /home/django/$APP_NAME/logs, outside the
# paths covered by the distro's own /etc/logrotate.d/nginx, so install a
# dedicated rotation rule for them.
sed "s/XXapp/$APP_NAME/g" "$(dirname "$0")/logrotate_nginx" > "/etc/logrotate.d/$APP_NAME-nginx"
chmod 644 "/etc/logrotate.d/$APP_NAME-nginx"