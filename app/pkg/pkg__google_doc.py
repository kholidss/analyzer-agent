from google.oauth2 import service_account
from googleapiclient.discovery import build
from dataclasses import dataclass
import re

@dataclass
class WriteDocParam:
    content: str
    doc_title: str

class GoogleDocPkg:
    def __init__(self, path_service_account: str) -> None:
        self.path_service_account = path_service_account
        self.scopes = [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive'
        ]

        # Authenticate
        credentials = service_account.Credentials.from_service_account_file(
            self.path_service_account, scopes=self.scopes
        )

        self.doc_service = build('docs', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)

        self.result_doc_url_view: str = None
        self.result_doc_url_edit: str = None

        # Set document permission
        self.result_doc_permission_type: str = "anyone"
        # writer or reader
        self.result_doc_permission_role: str = "writer"

        self.font_family: str = "Times New Roman"
        self.font_size: int = 14


    def set_font_family(self, font_family: str):
        self.font_family = font_family

    def set_font_size(self, font_size: int):
        self.font_size = font_size

    def set_result_doc_permission_type(self, result_doc_permission_type: str):
         self.result_doc_permission_type = result_doc_permission_type

    def set_result_doc_permission_role(self, result_doc_permission_role: str):
         self.result_doc_permission_role = result_doc_permission_role

    def get_result_doc_url_view(self) -> str:
         return self.result_doc_url_view 
    
    def get_result_doc_url_edit(self) -> str:
         return self.result_doc_url_edit 
    
    def write_doc(self, param: WriteDocParam) :
        document = self.doc_service.documents().create(body={"title": param.doc_title}).execute()
        doc_id = document['documentId']

        clean_content = self._clean_content_from_markdown(param.content)

        self.doc_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [self._build_insert_request(1, clean_content), self._build_style_request(clean_content)]}
        ).execute()

        permission = {
            'type': self.result_doc_permission_type,
            'role': self.result_doc_permission_role
        }
        self.drive_service.permissions().create(fileId=doc_id, body=permission).execute()

        self.result_doc_url_edit = f"https://docs.google.com/document/d/{doc_id}/edit"
        self.result_doc_url_view = f"https://docs.google.com/document/d/{doc_id}/view"

        return self

    def _build_insert_request(self, index: int, content: str) -> dict:
        return {
            "insertText": {
                "location": {
                    "index": index
                },
                "text": content
            }
        }
    
    def _build_style_request(self, content: str) -> dict:
            return  {
                "updateTextStyle": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": 1 + len(content)
                    },
                    "textStyle": {
                        "fontSize": {
                            "magnitude": self.font_size,
                            "unit": "PT"
                        },
                        "weightedFontFamily": {
                            "fontFamily": self.font_family
                        }
                    },
                    "fields": "fontSize,weightedFontFamily"
                }
            }

    def _clean_content_from_markdown(self, text: str) -> str:
        text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)

        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
        text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
        text = re.sub(r'`(.*?)`', r'\1', text)        # `inline code`

        return text
    