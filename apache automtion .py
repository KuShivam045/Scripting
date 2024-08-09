import os
import subprocess

def main():
    # Prompt for domain name
    domain = input("Enter the domain name: ").strip()
    
    # Define the path for the configuration file
    config_file = f"/etc/apache2/sites-available/{domain}.conf"
    
    # Create the configuration file content
    config_content = f"""<VirtualHost *:80>
    ServerAdmin webmaster@{domain}
    ServerName {domain}
    ServerAlias {domain}
    DocumentRoot /var/www/{domain}
    ErrorLog ${{APACHE_LOG_DIR}}/{domain}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}_access.log combined
</VirtualHost>"""
    
    # Create the configuration file
    with open(config_file, 'w') as file:
        file.write(config_content)
    
    # Create the document root directory
    os.makedirs(f"/var/www/{domain}", exist_ok=True)
    
    # Set permissions (assuming www-data is the user running Apache)
    subprocess.run(['sudo', 'chown', '-R', 'www-data:www-data', f'/var/www/{domain}'])
    subprocess.run(['sudo', 'chmod', '-R', '755', f'/var/www/{domain}'])
    
    # Copy the default index.html to the new document root
    subprocess.run(['sudo', 'cp', '/var/www/html/index.html', f'/var/www/{domain}/'])
    
    # Enable the site by creating a symbolic link
    subprocess.run(['sudo', 'ln', '-s', config_file, '/etc/apache2/sites-enabled/'])
    
    # Test the configuration for syntax errors
    result = subprocess.run(['sudo', 'apache2ctl', 'configtest'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Apache configuration test failed:\n{result.stderr}")
        return
    
    # Reload Apache to apply the changes
    subprocess.run(['sudo', 'systemctl', 'reload', 'apache2'])
    
    # Obtain SSL certificate using Certbot
    result = subprocess.run(['sudo', 'certbot', '--apache', '-d', domain], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Certbot failed:\n{result.stderr}")
        return
    
    print(f"Configuration for {domain} created and enabled.")

if __name__ == "__main__":
    main()
