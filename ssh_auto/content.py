def index_html(domain_name):
    txt = f"""
        {domain_name} Configured Successfully!
        Your Apache virtual host is up and running."""
    return txt

def dirConf(directory_auth,domain_name):
    
    if directory_auth:
        context = f"""
<Directory /var/www/html/{domain_name}>
AuthType Basic
AuthName 'Restricted Area'
AuthUserFile /etc/apache2/sites-available/{domain_name}/.htpasswd
Require valid-user
</Directory>
""" 
        return context
    else:
        context = f"""
<Directory /var/www/html/{domain_name}>
Options Indexes FollowSymLinks
AllowOverride All
Require all granted
</Directory>
"""
        return context
    

def locationConf(auth,location, domain_name):
    
    if auth:
        context = f"""
<Location {location}>
AuthType Basic
AuthName 'Restricted Area'
AuthUserFile /etc/apache2/sites-available/{domain_name}/.htpasswd
Require valid-user
</Location>
"""
        return context
    else:
        context = f"""
<Location {location}>
# No authentication required
</Location>
"""
        return context

def virtualHostConf(directory,domain_name):
    
    context = f"""
<VirtualHost *:80>
ServerAdmin webmaster@{domain_name}
ServerName {domain_name}
ServerAlias {domain_name}
DocumentRoot /var/www/html/{domain_name}

# Including the custom directory block
Include {directory}directory.conf

# Including the custom location blocks
Include {directory}location.conf

# Logging configurations
ErrorLog {directory}error.log
CustomLog {directory}access.log combined
</VirtualHost>
"""
    return context