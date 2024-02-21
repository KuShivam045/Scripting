from azure.storage.blob import BlobServiceClient
import os


def list_blobs_flat(connection_string, container_name):

    blob_service_client = BlobServiceClient.from_connection_string(connection_string) 
    container_client = blob_service_client.get_container_client(container=container_name)
    blob_list = container_client.list_blobs()

    file_list = []
    for blob in blob_list:
        # blob_list.append(blob.name)
        # print(f"Name: {blob.name}")
        file_list.append(blob.name)
    print(file_list)

# def download_blob_to_file(container_name, blob_name, download_file_path, connection_string):

#     blob_service_client = BlobServiceClient.from_connection_string(connection_string) 
#     blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
#     with open(download_file_path, "wb") as file:
#         download_stream = blob_client.download_blob()
#         file.write(download_stream.readall())


connection_string = "DefaultEndpointsProtocol=https;AccountName=nothing;AccountKey=BSDKJVNKNJXCVKBJlksbjvJLKBHFJLVHLKbkvBJNlkbjvLKbvkB;EndpointSuffix=core.windows.net"
container_name = "test-donwloader"
# blob_name = "test.py"
# blob_name = "my-sql-connector.zip"
# download_dir = "downloads"
# download_file_path = os.path.join(download_dir, blob_name)

list_blobs_flat(connection_string, container_name)
# download_blob_to_file(container_name, blob_name, download_file_path, connection_string)