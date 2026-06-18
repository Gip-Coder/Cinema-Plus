import os
from fastapi import UploadFile
from backend.storage.storage_provider import StorageProvider
from backend.core.config import settings

class LocalStorageProvider(StorageProvider):
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir

    async def save(self, file: UploadFile, filename: str, folder: str = "media") -> str:
        folder_path = os.path.join(self.upload_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        
        # Read content and write
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        # Reset file seek for subsequent reads
        file.file.seek(0)
        
        return f"/{self.upload_dir}/{folder}/{filename}"

    def delete(self, key: str) -> None:
        # key is a relative path or filename inside a folder
        file_path = os.path.join(self.upload_dir, key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting local storage file {file_path}: {e}")

    def get_url(self, key: str) -> str:
        if key.startswith("/"):
            return key
        return f"/{self.upload_dir}/{key}"
