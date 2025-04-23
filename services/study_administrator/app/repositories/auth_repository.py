import os

from firebase_admin import firestore, auth

from app.core.firebase import FirebaseAdmin
from app.models.user import User


class AuthRepository:
    def __init__(self):
        self._firebase = FirebaseAdmin(os.getenv("GCP_PROJECT_ID"))
        self.db = firestore.client()
        self.default_role = ("connecta-viewer",)

    def _get_user_metadata(self, user_id: str) -> dict:
        document = self.db.collection("users").document(user_id).get()
        return document.to_dict() if document.exists else {}

    def get_user_roles(self, user_id: str) -> tuple[str]:
        user_metadata = self._get_user_metadata(user_id)
        return tuple(user_metadata.get("roles", self.default_role))

    def get_user_delegates(self, user_id: str) -> tuple[str]:
        user_metadata = self._get_user_metadata(user_id)
        return tuple(user_metadata.get("delegates", []))

    def get_users(self) -> list[User]:
        users = []
        page = auth.list_users()

        while page:
            for user in page.users:
                users.append(
                    User(user_id=user.uid, name=user.display_name, email=user.email)
                )
            page = page.get_next_page()
        return users

    def get_user_name_from_id(self, user_id: str) -> str:
        user = auth.get_user(user_id)
        return user.display_name

    def get_user_id_from_name(self, user_name: str) -> str:
        users = self.get_users()
        for user in users:
            if user.name == user_name:
                return user.user_id
        return None
