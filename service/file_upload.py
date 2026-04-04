import boto3
import logging
from botocore.config import Config

def get_s3_client():
    s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
    return s3

def write_wav_to_s3(file_name, key_path):
    s3_client = get_s3_client()
    try:
        s3_client.generate_presigned_url(
            ClientMethod='put_object',  
            Params={'Bucket': 'neuro-audio-bucket', 'Key': key_path}, 
            ExpiresIn=3600
        )
        logging.info("[File Upload] Created S3 Presigned URL.")
    except Exception as e:
        logging.error(f"[File Upload] Error uploading file: {e}")

def read_wav_from_s3(key_path, local_path):
    s3_client = get_s3_client()
    try:
        s3_client.download_file('neuro-audio-bucket', key_path, local_path)
        logging.info("[File Upload] File downloaded successfully.")
    except Exception as e:
        logging.error(f"[File Upload] Error downloading file: {e}")
