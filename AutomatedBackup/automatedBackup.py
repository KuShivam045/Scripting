import subprocess
import shutil
import os
import boto3

def local_backup(source_directory, destination_directory):
    try:
        # Use rsync for local backup
        subprocess.run(["rsync", "-av", source_directory, destination_directory])
        return True
    except Exception as e:
        print(f"Local backup failed: {e}")
        return False

def s3_backup(source_directory, bucket_name, aws_access_key_id, aws_secret_access_key):
    try:
        # Initialize S3 client
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

        # Iterate through files in the source directory and upload to S3
        for root, dirs, files in os.walk(source_directory):
            for file in files:
                file_path = os.path.join(root, file)
                s3.upload_file(file_path, bucket_name, file_path)

        return True
    except Exception as e:
        print(f"S3 backup failed: {e}")
        return False

def main():
    # Set your source directory
    source_directory = "/home/ubuntu/wisecow"

    # Set your local backup destination
    local_destination_directory = "/BackupOfWisecow"

    # Set your S3 bucket name and credentials
    s3_bucket_name = "cicd-terraform-vpc"
    aws_access_key_id = "AKIAYS2NRDJ7LRHFFWFN"
    aws_secret_access_key = "LbQKEdUj6itxi9T6M41CrGfpGD3ejFewaqACRP97"

    # Local Backup
    if local_backup(source_directory, local_destination_directory):
        print("Local backup successful")
    else:
        print("Local backup failed")

    # S3 Backup
    if s3_backup(source_directory, s3_bucket_name, aws_access_key_id, aws_secret_access_key):
        print("S3 backup successful")
    else:
        print("S3 backup failed")

if __name__ == "__main__":
    main()
