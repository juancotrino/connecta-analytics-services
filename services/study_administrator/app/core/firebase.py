import firebase_admin


class FirebaseAdmin:
    _instances = {}  # Dictionary to store instances per project

    def __new__(cls, project_id: str):
        if project_id not in cls._instances:
            cls._instances[project_id] = super(FirebaseAdmin, cls).__new__(cls)
            cls._instances[project_id]._initialize(project_id)
        return cls._instances[project_id]

    def _initialize(self, project_id: str):
        if (
            project_id not in firebase_admin._apps
        ):  # Ensure Firebase is initialized only once per project
            app_options = {"projectId": project_id}
            firebase_admin.initialize_app(options=app_options)
