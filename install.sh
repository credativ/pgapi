#!/bin/bash

#
# Warning! Just for personal testing usage
#

# local debugging
apt-get -y install jq curl vim rsync

# system- and required python-packages
apt-get -y install apache2 postgresql-common gnupg sudo libjson-perl
apt-get -y install python3-waitress python3-psutil python3-flask python3-flask-restful python3-yaml

# install pgcommon and postgresql-12
/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
apt install -y postgresql-12 pgbackrest

# activate apache2 proxy
cp conf/pgapi-apache2.conf /etc/apache2/conf-available/pgapi.conf
a2enmod proxy_http
a2enconf pgapi
systemctl restart apache2

# sudoers for postgres-user
cp conf/pgapi.sudoers /etc/sudoers.d/pgapi
chmod 0440 /etc/sudoers.d/pgapi

# copy code to python-package-path
cp -r pgapi /usr/lib/python3/dist-packages/

# create user-service for pgapi for user postgres
su - postgres -c "mkdir -p ~/.config/systemd/user/"
cp conf/pgapi.service ~postgres/.config/systemd/user/
chown -R postgres.postgres ~postgres/.config/systemd
ln -s /var/lib/postgresql/.config/systemd/user/multi-user.target.wants/pgapi.service /var/lib/postgresql/.config/systemd/user/pgapi.service.

# enable journald for postgres-user
usermod -a -G systemd-journal postgres

systemctl --user enable pgapi
