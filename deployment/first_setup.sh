#!/bin/bash
adduser django
usermod -aG sudo django
mkdir /home/django/.ssh
cp ~/.ssh/authorized_keys /home/django/.ssh
chown -R django:django /home/django
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
service ssh restart