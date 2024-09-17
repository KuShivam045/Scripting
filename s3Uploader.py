import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def upload_image_to_s3(file_path, bucket_name, s3_file_key, aws_access_key_id, aws_secret_access_key):
    try:
        # Initialize a session using Amazon S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        # Upload the file
        s3_client.upload_file(file_path, bucket_name, s3_file_key)
        print("Upload Successful")
    
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")
    except PartialCredentialsError:
        print("Incomplete credentials provided")
    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example
file_path = r'C:\\Users\\JAM\Downloads\\321.jpg'  # Local file path
bucket_name = 'jammylko'   # S3 bucket name
s3_file_key = 'images/image.jpg'      # S3 file key (path in the bucket)
aws_access_key_id = 'Your_AWS_ACCESS_KEY_ID'
aws_secret_access_key = 'Your_AWS_SECRET_ACCESS_KEY'

upload_image_to_s3(file_path, bucket_name, s3_file_key, aws_access_key_id, aws_secret_access_key)
