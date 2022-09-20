# pip install azure-storage-blob
from azure.storage.blob import BlobServiceClient

blob_service_client = BlobServiceClient(
    account_url="https://indigentdefensepublic.blob.core.windows.net/"
)
blob_client = blob_service_client.get_blob_client(
    container="indigentdefensepublic", blob="test_write.txt"
)
blob_client.upload_blob("hello world")
