from azure.storage.blob import BlobServiceClient
import os

def download_blob_to_file(container_name, blob_name, download_file_path, connection_string):

    blob_service_client = BlobServiceClient.from_connection_string(connection_string) 
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    with open(download_file_path, "wb") as file:
        download_stream = blob_client.download_blob()
        file.write(download_stream.readall())


connection_string = "DefaultEndpointsProtocol=https;AccountName=Nothing;AccountKey=bnkhbjbhcajbhcsjkBJxbhjcbhjkdbhjhbZJBjbhcjsdh+nkbclkbhsdlklkcvkn==;EndpointSuffix=core.windows.net"
container_name = "test-downloader"

blob_name = "Zeal-Pic2.jpg"
download_dir = "downloads"
download_file_path = os.path.join(download_dir, blob_name)

download_blob_to_file(container_name, blob_name, download_file_path, connection_string)
