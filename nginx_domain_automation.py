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

    directory = "/etc/nginx/sites-available"
    try:
        if not os.path.exists(directory):
            return f"Directory '{directory}' does not exist."
        file_path = os.path.join(directory,filename)
        print(domain_name, "1111111111111111")
        content =f'''<VirtualHost *:80>
    ServerName {domain_name}
    ServerAlias www.{domain_name}
    Redirect permanent / http://www.{domain_name}/
</VirtualHost>'''

        # Use sudo to write the file
        command = f'echo "{content}" | sudo tee {file_path}'
        subprocess.run(command, shell=True, check=True)

       # If the file creation was successful, create the symbolic link in sites-enabled
        command = f'sudo ln -s {file_path} /etc/nginx/sites-enabled/{filename}'
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

        return (f"File {filename} created successfully in {directory}, "
                f"symbolic link created in /etc/nginx/sites-enabled, "
                f"permissions set, and index.html copied to /var/www/html/{domain_name} .")

    except subprocess.CalledProcessError:
        return f"Permission denied to access '{directory}'"

    except Exception as e:
        return str(e)

@app.route('/create', methods=['POST'])
def create_file():
    data = request.json
    domain_name = data.get('domain_name', '.')
    filename = data.get('filename')

    if not filename:
        return jsonify({"error": "Filename is required."}),400

    result = create_file_in_directory(domain_name,filename)
    return jsonify({"message": result})

if __name__=='__main__':
    app.run('0.0.0.0', port=8000, debug=True)
