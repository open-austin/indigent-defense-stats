from creds import aws_access_key, aws_secret_access_key, bucketname
from io import BytesIO
import boto3
import typing


if aws_secret_access_key:

    s3 = boto3.client(
        "s3",
        region_name="us-east-2",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key,
    )

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucketname, prefix=)

    for page in pages:
        existing_files = {obj["Key"] for obj in page["Contents"]}

else: 
    existing_files = {}

def s3_get_folder_contents(folderpath: str) -> set : 
    """
    Get all keys starting with a prefix (or files in a folder if no aws key)

    Args:
        folderpath (str): Prefix to search folder

    Returns:
        set: set of all files in folder
        
    """
    # If no access key stored, look in local foldedr
    if not aws_access_key: 
        return 



def s3_write_html(
    filepath: str,
    filebody: str,
    existing_files: set = existing_files,
    aws_access_key_id: str = aws_access_key,
    aws_secret_access_key: str = aws_secret_access_key,
) -> None:
    """writes file to s3 bucket if access keys are available. Otherwrite, writes locally

    Args:
        filepath (str): Path to write html file to.
        filebody (str): Body of html file
        aws_access_key_id (str): Access key to work with s3
        aws_secret_access_key (str):  Access key to work with s3
    """
    # If no access key stored, save locally
    if not aws_access_key:
        with open(filepath, "w") as f:
            f.write(filebody)
        return None

    # If file already exists, skip
    if filepath in existing_files:
        print("file already exists")
        return None

    # Write to s3 bucket
    s3 = boto3.client(
        "s3",
        region_name="us-east-2",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key,
    )
    s3.upload_fileobj(BytesIO(filebody.encode("UTF-8")), bucketname, filepath)
    return None

def s3_read_html(
    filepath: str,
    aws_access_key_id: str = aws_access_key,
    aws_secret_access_key: str = aws_secret_access_key,
) -> None:
    """reads file from s3 bucket if access keys are available. Otherwrite, reads locally

    Args:
        filepath (str): Path to read html file from.
        aws_access_key_id (str): Access key to work with s3
        aws_secret_access_key (str):  Access key to work with s3
    """
    # If no access key stored, save locally
    if not aws_access_key:
        with open(filepath, "r") as f:
            html_str = f.read()
        return html_str

    # Read from s3 bucket
    s3 = boto3.client(
        "s3",
        region_name="us-east-2",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_access_key,
    )
    
    object_content = s3.get_object(Bucket=bucketname, Key=filepath)
    html_str = object_content['Body'].read()
    return html_str