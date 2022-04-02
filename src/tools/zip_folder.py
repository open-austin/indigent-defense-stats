import zipfile
import os
import argparse
from io import BytesIO
import boto3

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-county",
    "-c",
    type=str,
    default="hays",
    help="The name of the county.",
)
argparser.description = "Print stats for the specified county."
args = argparser.parse_args()

folderpath = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", args.county, "case_html"
)
memory_file = BytesIO()
with zipfile.ZipFile(memory_file, "w") as zf:
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
