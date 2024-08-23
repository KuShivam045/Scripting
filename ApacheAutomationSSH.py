import paramiko
import os
import subprocess
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def execute_ssh_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    print(command)
    # Read stdout and stderr
    output = stdout.read().decode()
    error = stderr.read().decode()
    # print(output, "\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"")
    # print(error, "/////////////////////////////////")
    # Get the exit status
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        raise Exception(f"Command '{command}' failed with exit status {exit_status} and error: {error}")
    
    return output

def ssh_connect(hostname, port, ssh_user, pem_file_path):
        # Setup SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(pem_file_path)
    ssh_client.connect(hostname=hostname, port=port, username=ssh_user, pkey=private_key)
 
    return ssh_client


def list_files_in_directory(domain_name):
    directory = "/etc/apache2/sites-available"
    try:
        files = os.listdir(directory)

        for file in files:
            if file == domain_name:
                return True
        return False
    except Exception as e:
        return {"error": str(e)}

def create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword, htpasswd_file):
    execute_ssh_command(remote_server ,f'sudo htpasswd -c -b {htpasswd_file} {baseAuthUsername} {baseAuthPassword}')
    # print(f"htpasswd is created")


def create_file_in_directory(remote_server, domain_name, directory_auth, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword):
    
    directory = f"/etc/apache2/sites-available/{domain_name}/"
    htpasswd_file = f"/etc/apache2/sites-available/{domain_name}/.htpasswd"
    execute_ssh_command(remote_server,f'sudo mkdir -p {directory}')

    try:
        # Generate directory configuration
        if directory_auth:
            create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword, htpasswd_file)
            dir_config_content = f"""
<Directory /var/www/html/{domain_name}>
AuthType Basic
AuthName 'Restricted Area'
AuthUserFile {directory}/.htpasswd
Require valid-user
</Directory>
"""
        else:
            dir_config_content = f"""
<Directory /var/www/html/{domain_name}>
Options Indexes FollowSymLinks
AllowOverride All
Require all granted
</Directory>
"""

        file_path = os.path.join(directory, "directory.conf")
        # Escape double quotes inside dir_config_content
        escaped_content = dir_config_content.replace('"', '\\"')
        # Use a here document to write content to the file
        command = f"""
        sudo bash -c "cat > {file_path} <<EOF
        {escaped_content}
        "
        """
        try:
            # execute_ssh_command(remote_server,f'sudo bash -c "printf \'{escaped_content}\' > {file_path}"') 
            execute_ssh_command(remote_server,command) 
        except Exception as e:
            return f"Failed to create directory configuration: {e}"

        # Generate location configurations
        location_configs = []
        for location, auth in zip(url_locations, url_locations_auth):
            if auth:
                create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword,htpasswd_file)
                location_config = f"""
<Location {location}>
AuthType Basic
AuthName 'Restricted Area'
AuthUserFile {directory}/.htpasswd
Require valid-user
</Location>
"""
            else:
                location_config = f"""
<Location {location}>
# No authentication required
</Location>
"""
            location_configs.append(location_config)

        combined_config = "\n".join(location_configs)
        file_path = os.path.join(directory, "location.conf")
        try:

            # Escape double quotes inside dir_config_content
            escaped_content = combined_config.replace('"', '\\"')

            execute_ssh_command(remote_server,f'sudo bash -c "printf \'{combined_config}\' > {file_path}"') 
            # print('location.conf is created')
        except Exception as e:
            return f"Failed to create location configuration: {e}"

        # Generate virtual host configuration

        filename = f"{domain_name}.conf"
        file_path = os.path.join(directory, filename)
        content = f'''
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
'''
        # # command = f'echo "{content}" | sudo tee {file_path}'


        # Check if the directory exists on the remote server
        # print('checking the existing path')
        try:
            check_directory_command = f'test -d {directory}'
            execute_ssh_command(remote_server, check_directory_command)
        except Exception as e:
            return f"Directory '{directory}' does not exist on the remote server: {e}"

        # print('creating the virtual host...')
        try:
            execute_ssh_command(remote_server, f'sudo bash -c "printf \'{content}\' > {file_path}"')
        except Exception as e:
            return f"Failed to create virtual host configuration: {e}"

        # print("Virtual host configuration created successfully.")

        # Create symbolic link in sites-enabled
        try:
            execute_ssh_command(remote_server, f'sudo mkdir /etc/apache2/sites-enabled/{domain_name}')
        except Exception as e:
            return f"Failed to create directory '/etc/apache2/sites-enabled/{domain_name}': {e}"

        # print("+++++++++++++++++++++++++++++")

        try:
            # List files in the remote directory
            list_files_command = f'ls {directory}'
            files_output = execute_ssh_command(remote_server, list_files_command)
            # print("&&&&&",files_output)
            # Assuming files_output contains the list of files as a string, split by newline
            files = files_output.strip().split('\n')
            # print("##########%",files)

            for i, file in enumerate(files):
                try:
                    command = f'sudo ln -s {directory}/{file} /etc/apache2/sites-enabled/{domain_name}/{file}'
                    execute_ssh_command(remote_server, command)
                except Exception as e:
                    return f"Failed to create symbolic link for file {file}: {e}"

        except Exception as e:
            return f"Failed to list files in directory '{directory}': {e}"

        # Create web root directory and set permissions
        try:
            command = f'sudo mkdir /var/www/html/{domain_name}'
            execute_ssh_command(remote_server, command)
        except Exception as e:
            return f"Failed to create web root directory: {e}"
        # print("Webroot Directory is created...")

        permission_commands = [
            f'sudo chown -R www-data:www-data /var/www/html/{domain_name}',
            f'sudo chmod -R 755 /var/www/html/{domain_name}',
            f'sudo cp /var/www/html/index.html /var/www/html/{domain_name}/'
        ]

        for cmd in permission_commands:
            try:
                execute_ssh_command(remote_server, cmd)
            except Exception as e:
                return f"Failed to execute permission command '{cmd}': {e}"
            # print(cmd,"Executed Successfully...")


            # Test the Apache configuration
        try:
            # print("Checking the Apache Config... ")
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            # print("Config checked now restarting Apache2 server... ")
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
            # print("Apache2 server restarted... ")
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
    # Verify HTTP response
        try:
            # print("requesting the url:  http://{domain_name} ... ")
            execute_ssh_command(remote_server, f'curl http://{domain_name}')
            # print("url:  http://{domain_name}  working fine... ")
        except Exception as e:
            return f"HTTP request failed: {e}"


        # Create symbolic links for logs
        try:
            # print("Creating the symlink for log files...")
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/access.log /etc/apache2/sites-enabled/{domain_name}/access.log')
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/error.log /etc/apache2/sites-enabled/{domain_name}/error.log')
            # print("Symlink for log files created successfully...")
        except Exception as e:
            return f"Failed to create symbolic link for logs: {e}"

        # Obtain SSL certificate using Certbot
        try:
            # print("Installing the SSL using Certbot... ")
            # execute_ssh_command(remote_server, f'sudo certbot --apache -d {domain_name}')
            execute_ssh_command(remote_server, f'sudo certbot --apache -d {domain_name} --non-interactive --agree-tos --no-eff-email --force-renewal')

            # print("SSL created successfully... ")
        except Exception as e:
            return f"Certbot failed: {e}"



        # Move SSL configuration
        try:
            execute_ssh_command(remote_server, f'sudo mv /etc/apache2/sites-enabled/{domain_name}-le-ssl.conf /etc/apache2/sites-enabled/{domain_name}/')
            # print("Moving the SSL config file into Domain directory... ")
        except Exception as e:
            return f"Failed to move SSL configuration: {e}"


        # Final configuration test and reload
        try:
            # print("Checking the Apache Config... ")
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            # print("Config checked now restarting Apache2 server... ")
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
            # print("Apache2 server restarted... ")
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
        
        return (f"File {filename} created successfully in {directory},\n"
                f"symbolic link created in /etc/apache2/sites-enabled,\n"
                f"permissions set, index.html copied to /var/www/html/{domain_name},\n"
                f"Apache configuration tested, Apache reloaded,\n"
                f"SSL configured using certbot,\n")

    except Exception as e:
        return str(e)
        


@app.route('/create', methods=['POST'])
def create_file():
    hostname = request.form['hostname']
    port = int(request.form['port'])
    ssh_user = request.form['ssh_user']
    domain_name = request.form['domain_name']
    directory_auth = request.form['directory_auth']
    url_locations = json.loads(request.form['url_locations'])
    url_locations_auth = json.loads(request.form['url_locations_auth'])
    # Handle file upload
    pem_file = request.files['pem_file']
    pem_file_path = os.path.join(".", pem_file.filename)
    pem_file.save(pem_file_path)

    # Validate input data
    if not hostname:
        return jsonify({"error": "Domain name is required."}), 400
    if not port:
        return jsonify({"error": "PORT is required."}), 400
    if not ssh_user:
        return jsonify({"error": "SSH User Name is required."}), 400
    if not pem_file_path:
        return jsonify({"error": "SSH Key is required."}), 400
    if not domain_name:
        return jsonify({"error": "Domain name is required."}), 400
    if not directory_auth:
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
    baseAuthUsername = None
    baseAuthPassword = None
    
    if directory_auth or url_locations_auth:
        baseAuthUsername = request.form['baseAuthUsername']
        baseAuthPassword = request.form['baseAuthPassword']

        # Validate username and password
        if not baseAuthUsername or not baseAuthPassword:
            return jsonify({"error": "Username and password are required for directory authorization."}), 400
 
    
    # Proceed with file creation
    remote_server = ssh_connect(hostname, port, ssh_user, pem_file_path)
    result = create_file_in_directory(remote_server, domain_name, directory_auth, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword)
    # Optionally, delete the .pem file after use
    os.remove(pem_file_path)

    return jsonify({"message": "Apache setup completed successfully"}, result), 200


if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=True)
