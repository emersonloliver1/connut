from abc import ABC, abstractmethod
import json
import base64
import os
from supabase import create_client
from supabase_config import supabase

class DocumentStorage(ABC):
    @abstractmethod
    def save(self, doc_id, content):
        pass

    @abstractmethod
    def get(self, doc_id):
        pass

    @abstractmethod
    def delete(self, doc_id):
        pass

class LocalJSONStorage(DocumentStorage):
    def __init__(self, file_path='storage/documents.json'):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                json.dump({}, f)

    def save(self, doc_id, content):
        with open(self.file_path, 'r+') as f:
            data = json.load(f)
            data[str(doc_id)] = base64.b64encode(content).decode('utf-8')
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    def load(self, doc_id):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
            encoded_content = data.get(str(doc_id))
            if encoded_content:
                return base64.b64decode(encoded_content)
        return None

    def delete(self, doc_id):
        with open(self.file_path, 'r+') as f:
            data = json.load(f)
            if str(doc_id) in data:
                del data[str(doc_id)]
                f.seek(0)
                json.dump(data, f)
                f.truncate()

    def get(self, doc_id):
        return self.load(doc_id)

class SupabaseStorage:
    def __init__(self, bucket_name='documentos'):
        self.bucket_name = bucket_name

    def save(self, file_path, file_content):
        try:
            supabase.storage.from_(self.bucket_name).upload(
                file_path,
                file_content
            )
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {str(e)}")
            return False

    def get(self, file_path):
        try:
            return supabase.storage.from_(self.bucket_name).download(file_path)
        except Exception as e:
            print(f"Erro ao recuperar arquivo: {str(e)}")
            return None

    def delete(self, file_path):
        try:
            supabase.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            print(f"Erro ao excluir arquivo: {str(e)}")
            return False