PROJECT_NAME = conteur
SOURCE_DIR = conteur
INSTALL_DIR := /opt/bin/$(PROJECT_NAME)
DATA_PATH := /shared/conteur
SERVICE_FILEPATH := /etc/systemd/system/$(PROJECT_NAME).service

# code #####################################################################
install_source: $(INSTALL_DIR)
	
$(INSTALL_DIR): $(SOURCE_DIR)
	mkdir -p $@
	cp -r $^/. $@
	# chmod +x $(INSTALLDIR)/$(PROJECTNAME)/__main__.py

uninstall_source:
	rm -rf $(INSTALL_DIR)

# config #####################################################################
install_config: $(DATA_PATH)

$(DATA_PATH): config.ini
	mkdir -p $@/voices $@/disks
	cp $^ $@
	
uninstall_config:
	rm -rf $(DATA_PATH)/config.ini

# service #####################################################################
install_service: $(SERVICE_FILEPATH)

$(SERVICE_FILEPATH): conteur.service
	cp $< $@
	chmod +x $@
	systemctl enable $(PROJECT_NAME)
	systemctl start $(PROJECT_NAME)

uninstall_service:
	systemctl stop $(PROJECT_NAME)
	systemctl disable $(PROJECT_NAME)
	rm $(SERVICE_FILEPATH)

# all #####################################################################
install: install_source install_config install_service
uninstall: uninstall_source uninstall_config uninstall_service
update: install_source
