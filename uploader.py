import os
import sys
from azure.storage.blob import BlobServiceClient

def upload_blob_file(connection_string, container_name: str, upload_file_path,blob_name):
    
    blob_service_client = BlobServiceClient.from_connection_string(connection_string) 

    container_client = blob_service_client.get_container_client(container=container_name)
    with open(upload_file_path, "rb") as data:
        blob_client = container_client.upload_blob(blob_name, data=data, overwrite=True)
        print("jvjvjvgvjvjvjvjv")



connection_string = "DefaultEndpointsProtocol=https;AccountName=wattson01;AccountKey=vgdscsdjcbsdbhcjasbhjkfbhasdjbhasdjbfhlsflshbdfljshdfglghlj==;EndpointSuffix=core.windows.net"
container_name = "wattson-update"
blob_name = sys.argv[1]
print("3656546465146=======================",blob_name)
blob = blob_name.split('\\')
blob_file = blob[-1]
upload_dir = "uploads"
upload_file_path = os.path.join(upload_dir, blob_name)

upload_blob_file(connection_string, container_name, upload_file_path,blob_file)