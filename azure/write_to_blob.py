from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential

# Authenticate to client
token_credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url="https://indigentdefensepublic.blob.core.windows.net/",
    credential=token_credential,
)

# Write to blob
blob_client = blob_service_client.get_blob_client(
    container="indigentdefensepublicblob", blob="test_write.txt"
)
if not blob_client.exists():
    blob_client.upload_blob("hello world")

# Read from blob
data = blob_client.download_blob()
print(data.readall())

# List blobs
container_client = blob_service_client.get_container_client(
    container="indigentdefensepublicblob"
)
blob_list = container_client.list_blobs()
for blob_name in blob_list:
    print(blob_name)
