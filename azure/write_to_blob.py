# pip install azure-storage-blob
# pip install azure-identity
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

token_credential = DefaultAzureCredential()

blob_service_client = BlobServiceClient(
    account_url="https://indigentdefensepublic.blob.core.windows.net/",
    credential=token_credential,
)

blob_client = blob_service_client.get_blob_client(
    container="indigentdefensepublicblob", blob="test_write.txt"
)
blob_client.upload_blob("hello world")
