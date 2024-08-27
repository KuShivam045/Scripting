def index_html(domain_name):
    txt = f"""
        {domain_name} Configured Successfully!
        Your virtual host is up and running."""
    return txt

################################### Config for Apache2 #############################################################


def apacheDirConf(directory_auth,domain_name):
    
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
    

def apacheLocationConf(auth,location, domain_name):
    
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

def apacheVirtualHostConf(directory,domain_name):
    
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



################################### Config for Nginx #############################################################


def nginxLocationConf(auth, location, domain_name):
    if auth:
        context = f"""
location {location} {{
    auth_basic "Restricted Area";
    auth_basic_user_file /etc/nginx/conf.d/{domain_name}.htpasswd;
}}
"""
    else:
        context = f"""
location {location} {{
    # No authentication required
}}
"""
    return context

def nginxVirtualHostConf(directory, domain_name):
    context = f"""
server {{
    listen 80;
    server_name {domain_name};

    root /var/www/html/{domain_name};
    index index.html;

    # Including the custom location blocks
    # include {directory}location.conf;

    # Logging configurations
    access_log {directory}access.log;
    error_log {directory}error.log;
}}
"""
    return context
