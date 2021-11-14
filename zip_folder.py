import zipfile
from io import BytesIO
import os
import boto3

folderpath = 'case_html'
memory_file = BytesIO()
with zipfile.ZipFile(memory_file, 'w') as zf:
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            filepath = os.path.join(root, file)
            zf.write(filepath, arcname=file)
memory_file.seek(0)

cli = boto3.client("s3")
cli.put_object(
    Body=memory_file,
    Bucket="indigent-defense",
    Key="case_html.zip",
)
