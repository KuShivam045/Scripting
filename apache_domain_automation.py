import os
import subprocess
from flask import Flask, request, jsonify


app = Flask(__name__)

def list_file_in_directory(directory):
    try:
        files = os.listdir(directory)
        return files
    except FileNotFoundError:
        return f"Directory '{directory}' not found."
    except PermissionError:
        return f"Permission denied to access '{directory}'"

@app.route('/', methods=['GET'])
def list_file():
    directory = request.args.get('directory', '.')
    files = list_file_in_directory(directory)
    return jsonify(files)

def create_file_in_directory(domain_name,filename):

    directory = "/etc/apache2/sites-available"
    try:
        if not os.path.exists(directory):
            return f"Directory '{directory}' does not exist."
        file_path = os.path.join(directory,filename)
        print(domain_name, "1111111111111111")
        content =f'''
<VirtualHost *:80>
    ServerAdmin webmaster@{domain_name}
    ServerName {domain_name}
    ServerAlias {domain_name}
    DocumentRoot /var/www/html/{domain_name}

    <Directory /var/www/html/{domain_name}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

</VirtualHost>
'''

        # Use sudo to write the file
        command = f'echo "{content}" | sudo tee {file_path}'
        subprocess.run(command, shell=True, check=True)

       # If the file creation was successful, create the symbolic link in sites-enabled
        command = f'sudo ln -s {file_path} /etc/apache2/sites-enabled/{filename}'
        subprocess.run(command, shell=True, check=True)
        
        #create a Webroot
        command = f'sudo mkdir /var/www/html/{domain_name}'
        subprocess.run(command, shell=True, check=True)

        # Set permissions and copy index.html
        permission_commands = [
            f'sudo chown -R www-data:www-data /var/www/html/{domain_name}',
            f'sudo chmod -R 755 /var/www/html/{domain_name}',
            f'sudo cp /var/www/html/index.html /var/www/html/{domain_name}/'
        ]
        
        for cmd in permission_commands:
            subprocess.run(cmd, shell=True, check=True)

        # Test the configuration for syntax errors
        command = 'sudo apache2ctl configtest'
        subprocess.run(command, shell=True, check=True)

        # Reload Apache to apply the changes
        command = 'sudo systemctl reload apache2'
        subprocess.run(command, shell=True, check=True)

        # Obtain SSL certificate using Certbot
        command = f'sudo certbot --apache -d {domain_name}'
        subprocess.run(command, shell=True, check=True)

        return (f"File {filename} created successfully in {directory}, \n"
                f"symbolic link created in /etc/apache2/sites-enabled, \n"
                f"permissions set, index.html copied to /var/www/html/{domain_name}, \n"
                f"Apache configuration tested, Apache reloaded, and SSL certificate obtained for {domain_name}.")
               

    # except subprocess.CalledProcessError:
    #     return f"Permission denied to access '{directory}'"

    except Exception as e:
        return str(e)

# @app.route('/create', methods=['POST'])
# def create_file():
#     data = request.json
#     domain_name = data.get('domain_name', '.')
#     filename = data.get('filename')
#     directoryAuth = data.get('directoryAuth', False)
#     url_location = data.get('url_location')
#     url_location_Auth = data.get('url_locationAuth', False)
#     custom_message = data.get('custom_message', '')

#     if not filename:
#         return jsonify({"error": "Filename is required."}), 400

#     # You can now use the additional input values in your logic
#     result = create_file_in_directory(domain_name, filename,directoryAuth, url_location,url_location_Auth, custom_message)
    
#     print(domain_name, filename,directoryAuth, url_location,url_location_Auth, custom_message)
#     return jsonify({"message": result})

@app.route('/create', methods=['POST'])
def create_file():
    data = request.json
    
    domain_name = data.get('domain_name')
    filename = data.get('filename')
    directoryAuth = data.get('directoryAuth')
    url_locations = data.get('url_locations')
    url_locations_Auth = data.get('url_locations_Auth')
    custom_message = data.get('custom_message')

    # Check if all required fields are present
    if not domain_name:
        return jsonify({"error": "Domain name is required."}), 400
    
    if not filename:
        return jsonify({"error": "Filename is required."}), 400
    
    if directoryAuth is None:
        return jsonify({"error": "Directory authorization (directoryAuth) is required."}), 400
    
    if not url_locations:
        return jsonify({"error": "At least one URL location is required."}), 400
    
    if not isinstance(url_locations, list) or not all(isinstance(loc, str) for loc in url_locations):
        return jsonify({"error": "URL locations must be a list of strings."}), 400
    
    if not isinstance(url_locations_Auth, list) or len(url_locations_Auth) != len(url_locations):
        return jsonify({"error": "URL location authorization must be a list with the same length as URL locations."}), 400
    
    if not custom_message:
        return jsonify({"error": "Custom message is required."}), 400

    # Proceed with your logic using the input values
    result = create_file_in_directory(domain_name, filename, directoryAuth, url_locations, url_locations_Auth, custom_message)
  
    return jsonify({"message": result})



if __name__=='__main__':
    app.run('0.0.0.0', port=8000, debug=True)
