from abc import ABC, abstractmethod
import json
import base64
import os

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

    def get(self, doc_id):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
            return base64.b64decode(data.get(str(doc_id), ''))

    def delete(self, doc_id):
        with open(self.file_path, 'r+') as f:
            data = json.load(f)
            if str(doc_id) in data:
                del data[str(doc_id)]
                f.seek(0)
                json.dump(data, f)
                f.truncate()

# Futura implementação para Google Cloud Storage
class GoogleCloudStorage(DocumentStorage):
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        # Inicializar cliente do Google Cloud Storage aqui

    def save(self, doc_id, content):
        # Implementar lógica de upload para o Google Cloud Storage
        pass

    def get(self, doc_id):
        # Implementar lógica de download do Google Cloud Storage
        pass

    def delete(self, doc_id):
        # Implementar lógica de exclusão do Google Cloud Storage
        pass