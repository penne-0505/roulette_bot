import os

import firebase_admin
import firebase_admin.firestore
from dotenv import load_dotenv
from firebase_admin import credentials
from model.model import Template, UserInfo


class DBManager:
    def __init__(self):
        load_dotenv()
        self.cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))

        firebase_admin.initialize_app(self.cred)

        self.db = firebase_admin.firestore.client()
        self.ref = self.db.collection("users")

    def _validate_user(self, data: dict) -> bool:
        return data["id"] is not None and data["name"] is not None

    def _validate_template(self, data: dict) -> bool:
        return (
            data["title"] is not None
            and data["id"] is not None
            and data["choices"] is not None
        )

    def _template_to_dict(self, template: Template) -> dict:
        return {
            "title": template.title,
            "id": template.id,
            "choices": template.choices,
        }

    def _dict_to_template(self, data: dict) -> Template:
        if not self._validate_template(data):
            raise ValueError("Invalid template data")

        return Template(
            title=data["title"],
            id=data["id"],
            choices=data["choices"],
        )

    def set_user(self, user: UserInfo) -> None:
        # fmt: off
        least_template = self._template_to_dict(user.least_template) if user.least_template is not None else None

        custom_templates = [self._template_to_dict(template) for template in user.custom_templates]
        # fmt: on

        try:
            self.ref.document(str(user.id)).set(
                {
                    "ds_name": user.name,
                    "id": user.id,
                    "least_template": least_template,
                    "custom_templates": custom_templates,
                }
            )
        except Exception:
            raise

    def get_user(self, user_id: int) -> UserInfo:
        try:
            doc = self.ref.document(str(user_id)).get()
            data = doc.to_dict()

            if data is None:
                return None

            least_template = (
                self._dict_to_template(data["least_template"])
                if data.get("least_template")
                else None
            )

            custom_templates = [
                self._dict_to_template(template_data)
                for template_data in (data.get("custom_templates") or [])
            ]

            return UserInfo(
                ds_user_id=data["ds_user_id"],
                name=data["ds_name"],
                id=data["id"],
                least_template=least_template,
                custom_templates=custom_templates,
            )

        except Exception:
            raise

    def delete_user(self, user_id: int) -> None:
        try:
            self.ref.document(str(user_id)).delete()
        except Exception:
            raise

    def add_custom_template(self, user_id: int, template: Template) -> None:
        try:
            user = self.get_user(user_id)
            user.custom_templates.append(template)
            self.set_user(user)
        except Exception:
            raise

    def delete_custom_template(self, user_id: int, template_id: str) -> None:
        try:
            user = self.get_user(user_id)
            user.custom_templates = [
                template
                for template in user.custom_templates
                if template.id != template_id
            ]
            self.set_user(user)
        except Exception:
            raise

    def set_least_template(self, user_id: int, template: Template) -> None:
        try:
            user = self.get_user(user_id)
            user.least_template = template
            self.set_user(user)
        except Exception:
            raise


if __name__ == "__main__":
    db_manager = DBManager()
    user = UserInfo(
        id=1,
        name="test",
        least_template=Template(title="test", choices=["test"]),
        custom_templates=[Template(title="test", choices=["test"])],
    )
    db_manager.set_user(user)
    print(db_manager.get_user(1))
    db_manager.delete_user(1)
