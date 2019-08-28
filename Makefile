all:

PACKAGE=python3-pgapi
DPKG_VERSION=$(shell sed -ne '1s/.*(//; 1s/).*//p' debian/changelog)
PACKAGE_RELEASE=1
GITBRANCH=HEAD
RPMDIR=$(CURDIR)/rpm
TARBALL=$(RPMDIR)/SOURCES/$(PACKAGE)_$(DPKG_VERSION).tar

rpmbuild: $(TARBALL).xz
	rpmbuild -D"%_topdir $(RPMDIR)" --define='package_version $(DPKG_VERSION)' --define='package_release $(PACKAGE_RELEASE)' -ba rpm/$(PACKAGE).spec

tarball $(TARBALL).xz:
	mkdir -p $(dir $(TARBALL))
	rm -f $(TARBALL).xz
	git archive --prefix=$(PACKAGE)-$(DPKG_VERSION)/ $(GITBRANCH) > $(TARBALL)
	xz $(TARBALL)

