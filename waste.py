import bcrypt
import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def list_files():
    directory = "/etc/apache2/sites-available"
    try:
        files = os.listdir(directory)
        return jsonify(files)
    
    except FileNotFoundError:
        return f"Directory '{directory}' not found."
    
    except PermissionError:
        return f"Permission denied to access '{directory}'"


def list_files_in_directory(domain_name):
    directory = "/etc/apache2/sites-available"
    try:
        files = os.listdir(directory)

        for file in files:
            if file == f"{domain_name}.conf":
                return True
        return False
    except Exception as e:
        return {"error": str(e)}

def create_htpasswd(username, password, htpasswd_file):
    
# Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    print("=============",hashed_password)
    subprocess.run(['sudo', 'bash', '-c', f'echo "{username}:{hashed_password}" >> {htpasswd_file}'])

    

def create_file_in_directory(domain_name, directory_auth, url_locations, url_locations_auth, username, password):
    directory = "/etc/apache2/sites-available"
    event_dir = f"/etc/apache2/sites-available/events/{domain_name}/"
    htpasswd_file = f"/etc/apache2/sites-available/events/{domain_name}/.htpasswdd"
    subprocess.run(['sudo', 'mkdir', '-p', event_dir], check=True)
    
    try:
        # Generate directory configuration
        if directory_auth:
            create_htpasswd(username, password,htpasswd_file)
            dir_config_content = f"""
<Directory /var/www/html/{domain_name}>

    AuthType Basic
    AuthName 'Restricted Area'
    AuthUserFile {event_dir}/.htpasswd
    Require valid-user
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>"""
        else:
            dir_config_content = f"""
<Directory /var/www/html/{domain_name}>
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>"""

        file_path = os.path.join(event_dir, "directory.conf")
        subprocess.run(['sudo', 'bash', '-c', f'echo "{dir_config_content}" > {file_path}'], check=True)

        # Generate location configurations
        location_configs = []
        for location, auth in zip(url_locations, url_locations_auth):
            if auth:
                create_htpasswd(username, password,htpasswd_file)
                location_config = f"""
<Location {location}>
    AuthType Basic
    AuthName 'Restricted Area'
    AuthUserFile {event_dir}/.htpasswd
    Require valid-user
</Location>"""
            else:
                location_config = f"""
<Location {location}>
    # No authentication required
</Location>"""
            location_configs.append(location_config)

        combined_config = "\n".join(location_configs)
        file_path = os.path.join(event_dir, "location.conf")
        subprocess.run(['sudo', 'bash', '-c', f'echo "{combined_config}" > {file_path}'], check=True)

        # Generate virtual host configuration
        if not os.path.exists(directory):
            return f"Directory '{directory}' does not exist."
        filename = f"{domain_name}.conf"
        file_path = os.path.join(directory, filename)
        content = f'''
<VirtualHost *:80>
    ServerAdmin webmaster@{domain_name}
    ServerName {domain_name}
    ServerAlias {domain_name}
    DocumentRoot /var/www/html/{domain_name}

    # Including the custom directory block
    Include {event_dir}/directory.conf

    # Including the custom location blocks
    Include {event_dir}/location.conf

    # Logging configurations
    ErrorLog {event_dir}/error.log
    CustomLog {event_dir}/access.log combined
</VirtualHost>
'''
        command = f'echo "{content}" | sudo tee {file_path}'
        subprocess.run(command, shell=True, check=True)

        # Create symbolic link in sites-enabled
        command = f'sudo ln -s {file_path} /etc/apache2/sites-enabled/{filename}'
        subprocess.run(command, shell=True, check=True)

        # Create web root directory and set permissions
        command = f'sudo mkdir /var/www/html/{domain_name}'
        subprocess.run(command, shell=True, check=True)

        permission_commands = [
            f'sudo chown -R www-data:www-data /var/www/html/{domain_name}',
            f'sudo chmod -R 755 /var/www/html/{domain_name}',
            f'sudo cp /var/www/html/index.html /var/www/html/{domain_name}/'
        ]
        for cmd in permission_commands:
            subprocess.run(cmd, shell=True, check=True)

        # Test the Apache configuration
        subprocess.run('sudo apache2ctl configtest', shell=True, check=True)
        subprocess.run('sudo systemctl reload apache2', shell=True, check=True)

        return (f"File {filename} created successfully in {directory},\n"
                f"symbolic link created in /etc/apache2/sites-enabled,\n"
                f"permissions set, index.html copied to /var/www/html/{domain_name},\n"
                f"Apache configuration tested, Apache reloaded.")

    except subprocess.CalledProcessError:
        return f"Permission denied to access '{directory}'"
    except Exception as e:
        return str(e)

@app.route('/create', methods=['POST'])
def create_file():
    data = request.json
    

    domain_name = data.get('domain_name')
    directory_auth = data.get('directoryAuth')
    url_locations = data.get('url_locations')
    url_locations_auth = data.get('url_locations_Auth')

    # Validate input data
    if not domain_name:
        return jsonify({"error": "Domain name is required."}), 400
    if directory_auth is None:
        return jsonify({"error": "Directory authorization (directoryAuth) is required."}), 400
    if not url_locations:
        return jsonify({"error": "At least one URL location is required."}), 400
    if not isinstance(url_locations, list) or not all(isinstance(loc, str) for loc in url_locations):
        return jsonify({"error": "URL locations must be a list of strings."}), 400
    if not isinstance(url_locations_auth, list) or len(url_locations_auth) != len(url_locations):
        return jsonify({"error": "URL location authorization must be a list with the same length as URL locations."}), 400

    if list_files_in_directory(domain_name) is True:
        return jsonify({"message": "Domain already registered, Please go manual"})

    # If directoryAuth is true, ask for username and password
    username = None
    password = None
    
    if directory_auth or url_locations_auth:
        username = data.get('username')
        password = data.get('password')

        # Validate username and password
        if not username or not password:
            return jsonify({"error": "Username and password are required for directory authorization."}), 400

    
    # Proceed with file creation
    result = create_file_in_directory(domain_name, directory_auth, url_locations, url_locations_auth, username, password)
    return jsonify({"message": result})


if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=True)