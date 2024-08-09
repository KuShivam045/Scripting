#!/bin/bash

# Prompt for domain name
read -p "Enter the domain name: " DOMAIN

# Define the path for the configuration file
CONFIG_FILE="/etc/apache2/sites-available/$DOMAIN.conf"

# Create the configuration file
sudo cat <<EOL > $CONFIG_FILE
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
sudo mkdir -p /var/www/$DOMAIN

# Set permissions (assuming www-data is the user running Apache)
sudo chown -R www-data:www-data /var/www/$DOMAIN
sudo chmod -R 755 /var/www/$DOMAIN
sudo cp /var/www/html/index.html /var/www/$DOMAIN/

# Enable the site by creating a symbolic link
sudo ln -s $CONFIG_FILE /etc/apache2/sites-enabled/

# Test the configuration for syntax errors
sudo apache2ctl configtest

# Reload Apache to apply the changes
sudo systemctl reload apache2

# Obtain SSL certificate using Certbot
sudo certbot --apache -d $DOMAIN

echo "Configuration for $DOMAIN created and enabled."
