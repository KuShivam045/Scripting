from flask import Flask, request, jsonify
import os
import paramiko

app = Flask(__name__)

def execute_ssh_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    error = stderr.read().decode()
    if error:
        raise Exception(f"Command '{command}' failed with error: {error}")
    return stdout.read().decode()

def setup_apache_config(hostname, port, username, private_key_path, domain_name):
    try:
        # Setup SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        ssh_client.connect(hostname=hostname, port=port, username=username, pkey=private_key)

        directory = r"/home/ubuntu/"
        dir_config_content = f"""
<Directory /var/www/html/{domain_name}>
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
"""

        file_path = os.path.join(directory, "directory.conf")
        try:
            execute_ssh_command(ssh_client, f'echo "{dir_config_content}" | sudo tee {file_path}')
        except Exception as e:
            return f"Failed to create directory configuration: {e}"

    finally:
        # Close the connection
        ssh_client.close()

@app.route('/setup-apache', methods=['POST'])
def setup_apache():
    try:
        # Get form data
        hostname = request.form['hostname']
        port = int(request.form['port'])
        username = request.form['username']
        domain_name = request.form['domain_name']

        # Handle file upload
        pem_file = request.files['pem_file']
        pem_file_path = os.path.join(".", pem_file.filename)
        pem_file.save(pem_file_path)

        # Call the setup function with the uploaded .pem file
        setup_apache_config(hostname, port, username, pem_file_path, domain_name)

        # Optionally, delete the .pem file after use
        os.remove(pem_file_path)

        return jsonify({"message": "Apache setup completed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
