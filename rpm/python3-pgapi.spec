Name:           python3-pgapi
Version:        %{package_version}
Release:        %{package_release}%{?dist}
BuildArch:      noarch
Summary:        REST API for PostgreSQL
Packager:       Adrian Vondendriesch <adrian.vondendriesch@credativ.de>
License:        GPLv3+
URL:            https://packages.debian.org/sid/%{name}
Source0:        http://ftp.debian.org/debian/pool/main/p/%{name}/%{name}_%{version}.tar.xz
#BuildRequires:  python
Requires:       python2-flask-restful

%description
pgapi tries to be a simple but useful REST API for postgresql-common based
PostgreSQL Systems.  It offers a way to create, delete, and control
PostgreSQL clusters via HTTP requests.

%package -n apache2-pgapi
Summary: Apache2 integration files for python3-pgapi
Requires: httpd
%description -n apache2-pgapi
This package contains the necessary glue to access pgapi via Apache WSGI.
%post -n apache2-pgapi

%prep
# unpack tarball, ignoring the name of the top level directory inside
%setup -c
mv */* .

%build
python setup.py build

%install
rm -rf %{buildroot}
python setup.py install -O1 --skip-build --prefix /usr --root %{buildroot}
echo /usr/bin/pgapi >> files-python3-pgapi
echo /usr/lib/python2.7/site-packages/pgapi >> files-python3-pgapi
echo /usr/lib/python2.7/site-packages/pgapi-%{package_version}-py2.7.egg-info >> files-python3-pgapi

install -m644 -D conf/pgapi.conf %{buildroot}/etc/pgapi/pgapi.conf
echo /etc/pgapi/pgapi.conf >> files-python3-pgapi

install -m644 -D wsgi/pgapi.wsgi %{buildroot}/usr/lib/python2.7/site-packages/pgapi/pgapi.wsgi
echo /usr/lib/python2.7/site-packages/pgapi/pgapi.wsgi >> files-python3-pgapi

mkdir -p %{buildroot}/etc/httpd/conf.d
cp wsgi/pgapi-apache2.conf %{buildroot}/etc/httpd/conf.d
echo /etc/httpd/conf.d >> files-apache2-pgapi

%files -n python3-pgapi -f files-python3-pgapi
%files -n apache2-pgapi -f files-apache2-pgapi
