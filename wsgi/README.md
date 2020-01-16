# HOWTO enable pgapi in wsgi

## Description

WSGI configuration to use pgapi with apache2.

## Installation

It's expected that `pgapi` is already installed on the system.

Copy apache.conf to `/etc/apache2/conf-available/`:
`cp pgapi-apache2.conf /etc/apache2/conf-available/pgapi.conf`

Enable the new `pgapi` module and restart apache2:
`a2enconf pgapi`
`systemctl restart apache2`

The new pgapi module should be available under `http://<server_ip>/pgapi`.
