#!/bin/bash

# Ensure the script is run with sudo
if [ "$EUID" -ne 0 ]
then echo "Please run as root"
     exit
fi

# Prompt for domain name
read -p "Enter the domain name: " DOMAIN

# Define the path for the configuration file
CONFIG_FILE="/etc/apache2/sites-available/$DOMAIN.conf"

# Create the configuration file
cat <<EOL > $CONFIG_FILE
<VirtualHost *:80>
    ServerAdmin webmaster@$DOMAIN
    ServerName $DOMAIN
    ServerAlias $DOMAIN
    DocumentRoot /var/www/$DOMAIN
    ErrorLog \${APACHE_LOG_DIR}/$DOMAIN_error.log
    CustomLog \${APACHE_LOG_DIR}/$DOMAIN_access.log combined
</VirtualHost>
EOL

# Create the document root directory
mkdir -p /var/www/$DOMAIN

# Set permissions (assuming www-data is the user running Apache)
chown -R www-data:www-data /var/www/$DOMAIN
chmod -R 755 /var/www/$DOMAIN

# Enable the site by creating a symbolic link
ln -s $CONFIG_FILE /etc/apache2/sites-enabled/

# Test the configuration for syntax errors
apache2ctl configtest

# Reload Apache to apply the changes
systemctl reload apache2

echo "Configuration for $DOMAIN created and enabled."
