import paramiko
import os
import json
from flask import Flask, request, jsonify
from script import listApacheDomain, configApache, listNginxDomain, configNginx
app = Flask(__name__)

def ssh_connect(hostname, port, ssh_user, pem_file_path):
    # Setup SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(pem_file_path)
    ssh_client.connect(hostname=hostname, port=port, username=ssh_user, pkey=private_key)
 
    return ssh_client


###################################### Config for Apache2 #############################################################


@app.route('/apache_config', methods=['POST'])
def createApacheFile():
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
    # If directoryAuth is true, ask for username and password
    baseAuthUsername = None
    baseAuthPassword = None

    if isinstance(directory_auth, str):
        directory_auth = directory_auth.strip().lower() == "true"
    if directory_auth or url_locations_auth:
        baseAuthUsername = request.form['baseAuthUsername']
        baseAuthPassword = request.form['baseAuthPassword']

        # Validate username and password
        if not baseAuthUsername or not baseAuthPassword:
            return jsonify({"error": "Username and password are required for directory authorization."}), 400
   
    ## Creation SSH Client for remote Access 
    remote_server = ssh_connect(hostname, port, ssh_user, pem_file_path)
  
    try:
        if listApacheDomain(remote_server, domain_name):
            return jsonify({"message": "Domain already registered, Please go manual"})
        
        # Proceed with file creation
        message = configApache(remote_server, domain_name, directory_auth, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword)
        if "successfully" in message:
            return jsonify({"message": message}), 201
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)})
    
    finally:
        if remote_server:
            remote_server.close()
        os.remove(pem_file_path) # Optionally, delete the .pem file after use




###################################### Config for Nginx #############################################################


@app.route('/nginx_config', methods=['POST'])
def createNginxFile():
    hostname = request.form['hostname']
    port = int(request.form['port'])
    ssh_user = request.form['ssh_user']
    domain_name = request.form['domain_name']
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
    if not url_locations:
        return jsonify({"error": "At least one URL location is required."}), 400
    if not isinstance(url_locations, list) or not all(isinstance(loc, str) for loc in url_locations):
        return jsonify({"error": "URL locations must be a list of strings."}), 400
    if not isinstance(url_locations_auth, list) or len(url_locations_auth) != len(url_locations):
        return jsonify({"error": "URL location authorization must be a list with the same length as URL locations."}), 400
    # If directoryAuth is true, ask for username and password
    baseAuthUsername = None
    baseAuthPassword = None

    # if isinstance(directory_auth, str):
    #     directory_auth = directory_auth.strip().lower() == "true"
    if url_locations_auth:
        baseAuthUsername = request.form['baseAuthUsername']
        baseAuthPassword = request.form['baseAuthPassword']

        # Validate username and password
        if not baseAuthUsername or not baseAuthPassword:
            return jsonify({"error": "Username and password are required for directory authorization."}), 400
   
    ## Creation SSH Client for remote Access 
    remote_server = ssh_connect(hostname, port, ssh_user, pem_file_path)
  
    try:
        if listNginxDomain(remote_server, domain_name):
            return jsonify({"message": "Domain already registered, Please go manual"})
        
        # Proceed with file creation
        message = configNginx(remote_server, domain_name, url_locations, url_locations_auth, baseAuthUsername, baseAuthPassword)
        if "successfully" in message:
            return jsonify({"message": message}), 201
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)})
    
    finally:
        if remote_server:
            remote_server.close()
        os.remove(pem_file_path) # Optionally, delete the .pem file after use



        
if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=True)
