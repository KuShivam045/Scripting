import os
from content import index_html , dirConf, locationConf, virtualHostConf

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


def list_domain(remote_server,domain_name):
    directory = "/etc/apache2/sites-available"
    try:
        # List files in the directory on the remote server
        command = f'sudo bash -c "ls {directory}"'
        stdout = execute_ssh_command(remote_server, command)

        # Check if the domain_name is in the list of files
        files = stdout.splitlines()
        if domain_name in files:
            return True
        return False

    except Exception as e:
        return f"Failed to check domain existence: {e}"

def list_webroot(remote_server,domain_name):
    directory = "/var/www/html"
    try:
        # List files in the directory on the remote server
        command = f'sudo bash -c "ls {directory}"'
        stdout = execute_ssh_command(remote_server, command)

        # Check if the domain_name is in the list of files
        files = stdout.splitlines()
        if domain_name in files:
            return f"Webroot {directory} already exist "
        else:
            
            webroot = execute_ssh_command(remote_server,f'sudo mkdir -p {directory}/{domain_name}')
            permission_commands = [
            f'sudo chown -R www-data:www-data /var/www/html/{domain_name}',
            f'sudo chmod -R 755 /var/www/html/{domain_name}'
            ]

            for cmd in permission_commands:
                try:
                    execute_ssh_command(remote_server, cmd)
                except Exception as e:
                    return f"Failed to execute permission command '{cmd}': {e}"
                print(cmd,"Executed Successfully...")

            webroot_dir = f"/var/www/html/{domain_name}/"
            file_path = os.path.join(webroot_dir, "index.html")
            escaped_content = index_html(domain_name)
            command = f"""
            sudo bash -c "cat > {file_path} <<EOF
            {escaped_content}
            "
            """
            try:
                execute_ssh_command(remote_server,command) 
            except Exception as e:
                # return f"Failed to create directory configuration: {e}"
                return f"Webroot {webroot} created"

    except Exception as e:
        return f"Failed to check domain existence: {e}"

def create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword, htpasswd_file):
    execute_ssh_command(remote_server ,f'sudo htpasswd -c -b {htpasswd_file} {baseAuthUsername} {baseAuthPassword}')
    print(f"htpasswd is created")


def create_file_in_directory(remote_server, domain_name, directory_auth, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword):
    
    directory = f"/etc/apache2/sites-available/{domain_name}/"
    htpasswd_file = f"/etc/apache2/sites-available/{domain_name}/.htpasswd"
    execute_ssh_command(remote_server,f'sudo mkdir -p {directory}')

    try:
        # Generate directory configuration
        if directory_auth:
            create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword, htpasswd_file)
            dir_config_content = dirConf(directory_auth, domain_name)
            print("******************************   ")
        else:
            dir_config_content = dirConf(directory_auth,  domain_name)

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
                location_config = locationConf(auth,location, domain_name)
            else:
                location_config = locationConf(auth,location, domain_name)

            location_configs.append(location_config)

        combined_config = "\n".join(location_configs)
        file_path = os.path.join(directory, "location.conf")
        try:

            # Escape double quotes inside dir_config_content
            escaped_content = combined_config.replace('"', '\\"')
            execute_ssh_command(remote_server,f'sudo bash -c "printf \'{combined_config}\' > {file_path}"') 
            print('location.conf is created')
        except Exception as e:
            return f"Failed to create location configuration: {e}"

        # Generate virtual host configuration

        filename = f"{domain_name}.conf"
        file_path = os.path.join(directory, filename)
        content = virtualHostConf(directory,domain_name)

        print('creating the virtual host...')
        try:
            execute_ssh_command(remote_server, f'sudo bash -c "printf \'{content}\' > {file_path}"')
        except Exception as e:
            return f"Failed to create virtual host configuration: {e}"

        print("Virtual host configuration created successfully.")

        # Create symbolic link in sites-enabled
        try:
            execute_ssh_command(remote_server, f'sudo mkdir /etc/apache2/sites-enabled/{domain_name}')
        except Exception as e:
            return f"Failed to create directory '/etc/apache2/sites-enabled/{domain_name}': {e}"

        print("+++++++++++++++++++++++++++++")

        try:
            # List files in the remote directory
            list_files_command = f'ls {directory}'
            files_output = execute_ssh_command(remote_server, list_files_command)
            print("&&&&&",files_output)
            # Assuming files_output contains the list of files as a string, split by newline
            files = files_output.strip().split('\n')
            print("##########%",files)

            for i, file in enumerate(files):
                try:
                    command = f'sudo ln -s {directory}/{file} /etc/apache2/sites-enabled/{domain_name}/{file}'
                    execute_ssh_command(remote_server, command)
                except Exception as e:
                    return f"Failed to create symbolic link for file {file}: {e}"

        except Exception as e:
            return f"Failed to list files in directory '{directory}': {e}"

        # Create web root directory and set permissions
        
        list_webroot(remote_server,domain_name)

        # Test the Apache configuration
        try:
            print("Checking the Apache Config... ")
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            print("Config checked now restarting Apache2 server... ")
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
            print("Apache2 server restarted... ")
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
    # Verify HTTP response
        try:
            print("requesting the url:  http://{domain_name} ... ")
            execute_ssh_command(remote_server, f'curl http://{domain_name}')
            print("url:  http://{domain_name}  working fine... ")
        except Exception as e:
            return f"HTTP request failed: {e}"


        # Create symbolic links for logs
        try:
            print("Creating the symlink for log files...")
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/access.log /etc/apache2/sites-enabled/{domain_name}/access.log')
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/error.log /etc/apache2/sites-enabled/{domain_name}/error.log')
            print("Symlink for log files created successfully...")
        except Exception as e:
            return f"Failed to create symbolic link for logs: {e}"

        # Obtain SSL certificate using Certbot
        try:
            print("Installing the SSL using Certbot... ")
            execute_ssh_command(remote_server, f'sudo certbot --apache -d {domain_name} --non-interactive --agree-tos --no-eff-email --force-renewal')

            print("SSL created successfully... ")
        except Exception as e:
            return f"Certbot failed: {e}"



        # Move SSL configuration
        try:
            execute_ssh_command(remote_server, f'sudo mv /etc/apache2/sites-enabled/{domain_name}-le-ssl.conf /etc/apache2/sites-enabled/{domain_name}/')
            print("Moving the SSL config file into Domain directory... ")
        except Exception as e:
            return f"Failed to move SSL configuration: {e}"


        # Final configuration test and reload
        try:
            print("Checking the Apache Config... ")
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            print("Config checked now restarting Apache2 server... ")
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
            print("Apache2 server restarted... ")
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
        
        return (f"File {filename} created successfully in {directory},\n"
                f"symbolic link created in /etc/apache2/sites-enabled,\n"
                f"permissions set, index.html copied to /var/www/html/{domain_name},\n"
                f"Apache configuration tested, Apache reloaded,\n"
                f"SSL configured using certbot,\n")

    except Exception as e:
        return str(e)
        
