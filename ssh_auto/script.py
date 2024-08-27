import os
# from content import apacheDirConf, index_html, apacheLocationConf, apacheVirtualHostConf, nginxLocationConf, nginxVirtualHostConf
from content import *

def execute_ssh_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    print(command)
    # Read stdout and stderr
    output = stdout.read().decode()
    error = stderr.read().decode()

    # Get the exit status
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status != 0:
        raise Exception(f"Command '{command}' failed with exit status {exit_status} and error: {error}")
    
    return output

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




###################################### Config for Apache2 #############################################################

def listApacheDomain(remote_server,domain_name):
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
    

def configApache(remote_server, domain_name, directory_auth, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword):
    
    directory = f"/etc/apache2/sites-available/{domain_name}/"
    htpasswd_file = f"/etc/apache2/sites-available/{domain_name}/.htpasswd"
    execute_ssh_command(remote_server,f'sudo mkdir -p {directory}')

    try:
        # Generate directory configuration
        if directory_auth:
            create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword, htpasswd_file)
            dir_config_content = apacheDirConf(directory_auth, domain_name)
        else:
            dir_config_content = apacheDirConf(directory_auth,  domain_name)
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
            execute_ssh_command(remote_server,command) 
        except Exception as e:
            return f"Failed to create directory configuration: {e}"

        # Generate location configurations
        location_configs = []
        for location, auth in zip(url_locations, url_locations_auth):
            if auth:
                create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword,htpasswd_file)
                location_config = apacheLocationConf(auth,location, domain_name)
            else:
                location_config = apacheLocationConf(auth,location, domain_name)
            location_configs.append(location_config)
        combined_config = "\n".join(location_configs)
        file_path = os.path.join(directory, "location.conf")
        
        try:
            # Escape double quotes inside dir_config_content
            escaped_content = combined_config.replace('"', '\\"')
            command = f"""
        sudo bash -c "cat > {file_path} <<EOF
        {escaped_content}
        "
        """
            execute_ssh_command(remote_server,command) 
        except Exception as e:
            return f"Failed to create location configuration: {e}"

        # Generate virtual host configuration
        filename = f"{domain_name}.conf"
        file_path = os.path.join(directory, filename)
        content = apacheVirtualHostConf(directory,domain_name)

        try:
            execute_ssh_command(remote_server, f'sudo bash -c "printf \'{content}\' > {file_path}"')
        except Exception as e:
            return f"Failed to create virtual host configuration: {e}"

        # Create symbolic link in sites-enabled
        try:
            execute_ssh_command(remote_server, f'sudo mkdir /etc/apache2/sites-enabled/{domain_name}')
        except Exception as e:
            return f"Failed to create directory '/etc/apache2/sites-enabled/{domain_name}': {e}"

        try:
            # List files in the remote directory
            list_files_command = f'ls {directory}'
            files_output = execute_ssh_command(remote_server, list_files_command)
            files = files_output.strip().split('\n')
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
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
        
        # Verify HTTP response
        try:
            execute_ssh_command(remote_server, f'curl http://{domain_name}')
        except Exception as e:
            return f"HTTP request failed: {e}"

        # Create symbolic links for logs
        try:
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/access.log /etc/apache2/sites-enabled/{domain_name}/access.log')
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/error.log /etc/apache2/sites-enabled/{domain_name}/error.log')
        except Exception as e:
            return f"Failed to create symbolic link for logs: {e}"

        # Obtain SSL certificate using Certbot
        try:
            execute_ssh_command(remote_server, f'sudo certbot --apache -d {domain_name} --non-interactive --agree-tos --no-eff-email --force-renewal')
        except Exception as e:
            return f"Certbot failed: {e}"

        # Move SSL configuration
        try:
            execute_ssh_command(remote_server, f'sudo mv /etc/apache2/sites-enabled/{domain_name}-le-ssl.conf /etc/apache2/sites-enabled/{domain_name}/')
        except Exception as e:
            return f"Failed to move SSL configuration: {e}"

        # Final configuration test and reload
        try:
            execute_ssh_command(remote_server, 'sudo apache2ctl configtest')
            execute_ssh_command(remote_server, 'sudo systemctl reload apache2')
        except Exception as e:
            return f"Apache configuration test or reload failed: {e}"
        
        return (f"File {filename} created successfully in {directory},\n"
                f"symbolic link created in /etc/apache2/sites-enabled,\n"
                f"permissions set, index.html copied to /var/www/html/{domain_name},\n"
                f"Apache configuration tested, Apache reloaded,\n"
                f"SSL configured using certbot,\n")

    except Exception as e:
        return str(e)
        


################################### Config for Nginx #############################################################

def listNginxDomain(remote_server,domain_name):
    directory = "/etc/nginx/sites-available"
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
    


def configNginx(remote_server, domain_name, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword):
    
    directory = f"/etc/nginx/sites-available/{domain_name}/"
    htpasswd_file = f"/etc/nginx/sites-available/{domain_name}/.htpasswd"
    execute_ssh_command(remote_server,f'sudo mkdir -p {directory}')

    try:

        # # Generate location configurations
        # location_configs = []
        # for location, auth in zip(url_locations, url_locations_auth):
        #     if auth:
        #         create_htpasswd(remote_server, baseAuthUsername, baseAuthPassword,htpasswd_file)
        #         location_config = nginxLocationConf(auth,location, domain_name)
        #     else:
        #         location_config = nginxLocationConf(auth,location, domain_name)
        #     location_configs.append(location_config)
        # combined_config = "\n".join(location_configs)
        # file_path = os.path.join(directory, "location.conf")
        
        # try:
        #     # Escape double quotes inside dir_config_content
        #     escaped_content = combined_config.replace('"', '\\"')
        #     command = f"""
        # sudo bash -c "cat > {file_path} <<EOF
        # {escaped_content}
        # "
        # """
        #     execute_ssh_command(remote_server,command) 
        # except Exception as e:
        #     return f"Failed to create location configuration: {e}"

        # Generate virtual host configuration
        filename = f"{domain_name}.conf"
        file_path = os.path.join(directory, filename)
        content = nginxVirtualHostConf(directory,domain_name)

        try:
            execute_ssh_command(remote_server, f'sudo bash -c "printf \'{content}\' > {file_path}"')
        except Exception as e:
            return f"Failed to create virtual host configuration: {e}"

        # Create symbolic link in sites-enabled
        try:
            execute_ssh_command(remote_server, f'sudo mkdir /etc/nginx/sites-enabled/{domain_name}')
        except Exception as e:
            return f"Failed to create directory '/etc/nginx/sites-enabled/{domain_name}': {e}"

        try:
            # List files in the remote directory
            list_files_command = f'ls {directory}'
            files_output = execute_ssh_command(remote_server, list_files_command)
            files = files_output.strip().split('\n')
            for i, file in enumerate(files):
                try:
                    command = f'sudo ln -s {directory}/{file} /etc/nginx/sites-enabled/{domain_name}/{file}'
                    execute_ssh_command(remote_server, command)
                except Exception as e:
                    return f"Failed to create symbolic link for file {file}: {e}"

        except Exception as e:
            return f"Failed to list files in directory '{directory}': {e}"

        # Create web root directory and set permissions
        list_webroot(remote_server,domain_name)

        # Test the Apache configuration
        try:
            execute_ssh_command(remote_server, 'sudo nginx -t')
            execute_ssh_command(remote_server, 'sudo systemctl reload nginx')
        except Exception as e:
            return f"Nginx configuration test or reload failed: {e}"
        
        # Verify HTTP response
        try:
            execute_ssh_command(remote_server, f'curl http://{domain_name}')
        except Exception as e:
            return f"HTTP request failed: {e}"

        # Create symbolic links for logs
        try:
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/access.log /etc/nginx/sites-enabled/{domain_name}/access.log')
            execute_ssh_command(remote_server, f'sudo ln -s {directory}/error.log /etc/nginx/sites-enabled/{domain_name}/error.log')
        except Exception as e:
            return f"Failed to create symbolic link for logs: {e}"

        # Obtain SSL certificate using Certbot
        try:
            execute_ssh_command(remote_server, f'sudo certbot --nginx -d {domain_name} --non-interactive --agree-tos --no-eff-email --force-renewal')
        except Exception as e:
            return f"Certbot failed: {e}"

        # Final configuration test and reload
        try:
            execute_ssh_command(remote_server, 'sudo nginx -t')
            execute_ssh_command(remote_server, 'sudo systemctl reload nginx')
        except Exception as e:
            return f"Nginx configuration test or reload failed: {e}"
        
        return (f"File {filename} created successfully in {directory},\n"
                f"symbolic link created in /etc/nginx/sites-enabled,\n"
                f"permissions set, index.html copied to /var/www/html/{domain_name},\n"
                f"Nginx configuration tested, Nginx reloaded,\n"
                f"SSL configured using certbot,\n")

    except Exception as e:
        return str(e)
        

