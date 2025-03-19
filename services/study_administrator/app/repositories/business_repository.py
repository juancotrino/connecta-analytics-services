import os

from firebase_admin import firestore
from app.core.firestore import FirebaseAdmin


class BusinessRepository:
    def __init__(self):
        self._firebase = FirebaseAdmin(os.getenv("GCP_PROJECT_ID"))
        self.db = firestore.client()

    def get_business_data(self) -> dict[str, dict]:
        document = self.db.collection("settings").document("business_data").get()

        if document.exists:
            business_data = document.to_dict()
            return business_data
