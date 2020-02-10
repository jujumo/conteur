PROJECTNAME = jukebox
SOURCEDIR = source
INSTALLDIR := /opt

# code #####################################################################
install_script: $(SOURCEDIR)
	mkdir -p $(INSTALLDIR)/$(PROJECTNAME)
	cp -r $(SOURCEDIR)/. $(INSTALLDIR)/$(PROJECTNAME)
	chmod +x $(INSTALLDIR)/$(PROJECTNAME)/__main__.py

uninstall_script: $(INSTALLDIR)/$(PROJECTNAME)
	rm -rf $(INSTALLDIR)/$(PROJECTNAME)
	
# service #####################################################################
install_service: $(SOURCEDIR)/jukebox.service
	cp $< /etc/systemd/system/$(PROJECTNAME).service
	chmod +x /etc/systemd/system/$(PROJECTNAME).service
	systemctl enable $(PROJECTNAME)
	systemctl start $(PROJECTNAME)

uninstall_service: /etc/systemd/system/$(PROJECTNAME).service
	systemctl stop $(PROJECTNAME)
	systemctl disable $(PROJECTNAME)
	rm $^


install: install_script install_service
uninstall: uninstall_script uninstall_service
