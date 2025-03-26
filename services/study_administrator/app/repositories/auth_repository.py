import os

from firebase_admin import firestore
from app.core.firebase import FirebaseAdmin


class AuthRepository:
    def __init__(self):
        self._firebase = FirebaseAdmin(os.getenv("GCP_PROJECT_ID"))
        self.db = firestore.client()

    def get_user_roles(self, user_id: str) -> tuple[str]:
        document = self.db.collection("users").document(user_id).get()

        if document.exists:
            user_info = document.to_dict()
            roles = tuple(user_info["roles"])
        else:
            roles = ("connecta-viewer",)

        return roles
