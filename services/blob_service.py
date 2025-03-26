from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import os
from config.settings import Config


class BlobService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )

    def get_container_client(self, container_name):
        """Get a container client for a specific container or the default one"""
        return self.blob_service_client.get_container_client(container_name)

    def upload_image(self, image_data, blob_name, container_name=None):
        container_client = self.get_container_client(container_name)
        container_client.upload_blob(name=blob_name, data=image_data)

    def download_image(self, blob_name, container_name=None):
        try:
            container_client = self.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            return blob_client.download_blob().readall()
        except Exception as e:
            print(f"Error downloading image {blob_name}: {str(e)}")
            return None

    def list_images(self, container_name=None):
        container_client = self.get_container_client(container_name)
        return [blob.name for blob in container_client.list_blobs()]
