from __future__ import annotations

from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import App, credentials, firestore

import utils
from models.model import Template, UserInfo


class UserRepository:
    def __init__(self, db: firestore.firestore.Client) -> None:
        self.ref = db.collection("users")

    def create_document(self, doc_id, data: dict) -> None:
        try:
            doc = self.ref.document(str(doc_id))
            doc.set(data)
        except Exception:
            raise

    def read_document(self, doc_id: int) -> dict:
        try:
            doc = self.ref.document(str(doc_id)).get()
            return doc.to_dict()
        except Exception:
            raise

    def delete_document(self, doc_id: int) -> None:
        try:
            self.ref.document(str(doc_id)).delete()
        except Exception:
            raise


class InfoRepository:
    def __init__(self, db: firestore.firestore.Client) -> None:
        self.ref = db.collection("info")

    def create_document(self, doc_id, data: dict) -> None:
        try:
            doc = self.ref.document(str(doc_id))
            doc.set(data)
        except Exception:
            raise

    def read_document(self, doc_id: int) -> dict:
        try:
            doc = self.ref.document(str(doc_id)).get()
            return doc.to_dict()
        except Exception:
            raise

    def delete_document(self, doc_id: int) -> None:
        try:
            self.ref.document(str(doc_id)).delete()
        except Exception:
            raise


class DBManager(metaclass=utils.Singleton):
    def __init__(self) -> None:
        self._app: App | None = None
        self.db: firestore.firestore.Client | None = None
        self.user_repository: UserRepository | None = None
        self.info_repository: InfoRepository | None = None

    @classmethod
    def get_instance(cls) -> "DBManager":
        return cls()

    def initialize(self, credentials_source: dict[str, Any] | Path) -> None:
        if self._app is not None:
            raise RuntimeError("DBManager is already initialized")

        certificate_source: dict[str, Any] | str
        if isinstance(credentials_source, Path):
            certificate_source = str(credentials_source)
        else:
            certificate_source = credentials_source

        app = firebase_admin.initialize_app(
            credentials.Certificate(certificate_source)
        )
        self.with_app(app)

    def with_app(self, app: App) -> None:
        if self._app is not None and self._app is not app:
            raise RuntimeError(
                "DBManager is already initialized with a different Firebase app"
            )

        self._app = app
        self.db = firestore.client(app=app)
        self.user_repository = UserRepository(self.db)
        self.info_repository = InfoRepository(self.db)

    def _ensure_configured(self) -> None:
        if self.user_repository is None or self.info_repository is None or self.db is None:
            raise RuntimeError(
                "DBManager is not configured. Call initialize() or with_app() before use."
            )

    def _get_user_repository(self) -> UserRepository:
        self._ensure_configured()
        assert self.user_repository is not None
        return self.user_repository

    def _get_info_repository(self) -> InfoRepository:
        self._ensure_configured()
        assert self.info_repository is not None
        return self.info_repository

    def _validate_user(self, data: dict) -> bool:
        return data["id"] is not None and data["name"] is not None

    def _validate_template(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False

        if not isinstance(data.get("title"), str):
            return False

        choices = data.get("choices")
        if not isinstance(choices, list):
            return False

        return all(isinstance(choice, str) for choice in choices)

    def _template_to_dict(self, template: Template) -> dict[str, str | list[str]]:
        return {
            "title": template.title,
            "choices": template.choices,
        }

    def _dict_to_template(self, data: dict) -> Template:
        if not self._validate_template(data):
            raise ValueError("Invalid template data")
        return Template(
            title=data["title"],
            choices=data["choices"],
        )

    def _read_or_initialize_embed_mode(
        self, info_repository: InfoRepository
    ) -> tuple[dict[str, str], bool]:
        data = info_repository.read_document("embed_mode")
        should_initialize = not isinstance(data, dict) or "embed_mode" not in data
        if should_initialize:
            data = {"embed_mode": "compact"}
            info_repository.create_document("embed_mode", data)
        return data, should_initialize

    def _init_default_templates(self) -> None:
        info_repository = self._get_info_repository()
        default_templates = [
            Template(
                title="League of Legends",
                choices=["Top", "Jungle", "Mid", "ADC", "Support"],
            ),
            Template(
                title="Valorant",
                choices=["Duelist", "Initiator", "Controller", "Sentinel"],
            ),
        ]
        default_templates = [
            self._template_to_dict(template) for template in default_templates
        ]
        default_templates = {"default_templates": default_templates}
        info_repository.create_document("default_templates", default_templates)

    def get_default_templates(self) -> list[Template]:
        info_repository = self._get_info_repository()
        templates = info_repository.read_document("default_templates")
        templates = templates["default_templates"]  # list
        return [self._dict_to_template(t) for t in templates]

    def toggle_embed_mode(self) -> None:
        info_repository = self._get_info_repository()
        try:
            data, initialized = self._read_or_initialize_embed_mode(info_repository)
            if initialized:
                return
            if data["embed_mode"] == "compact":
                data["embed_mode"] = "detailed"
            else:
                data["embed_mode"] = "compact"
            info_repository.create_document("embed_mode", data)
        except Exception:
            raise

    def get_embed_mode(self) -> str:
        info_repository = self._get_info_repository()
        try:
            data, _ = self._read_or_initialize_embed_mode(info_repository)
            return data["embed_mode"]

        except Exception:
            raise

    def init_user(self, user_id: int, name: str) -> None:
        user_repository = self._get_user_repository()
        default_templates = self.get_default_templates()
        default_templates = [
            self._template_to_dict(template) for template in default_templates
        ]

        data = {
            "name": name,
            "id": user_id,
            "least_template": None,
            "custom_templates": default_templates,
        }
        try:
            user_repository.create_document(user_id, data)
        except Exception:
            raise

    # これいる？
    def set_user(self, user: UserInfo) -> None:
        user_repository = self._get_user_repository()
        least_template = (
            self._template_to_dict(user.least_template)
            if user.least_template is not None
            else None
        )
        custom_templates = [
            self._template_to_dict(template) for template in user.custom_templates
        ]
        data = {
            "name": user.name,
            "id": user.id,
            "least_template": least_template,
            "custom_templates": custom_templates,
        }
        try:
            user_repository.create_document(user.id, data)
        except Exception:
            raise

    def get_user(self, user_id: int) -> UserInfo:
        user_repository = self._get_user_repository()
        try:
            data = user_repository.read_document(user_id)
            if data is None:
                return None
            least_template = (
                self._dict_to_template(data["least_template"])
                if data.get("least_template")
                else None
            )
            custom_templates = [
                self._dict_to_template(t) for t in (data.get("custom_templates") or [])
            ]
            return UserInfo(
                id=data["id"],
                name=data["name"],
                least_template=least_template,
                custom_templates=custom_templates,
            )
        except Exception:
            raise

    def delete_user(self, user_id: int) -> None:
        user_repository = self._get_user_repository()
        try:
            user_repository.delete_document(user_id)
        except Exception:
            raise

    def user_is_exist(self, user_id: int) -> bool:
        try:
            user = self.get_user(user_id)
            return user is not None
        except Exception:
            return False

    def add_custom_template(self, user_id: int, template: Template) -> None:
        if not self.user_is_exist(user_id):
            raise ValueError("User not found")

        try:
            user = self.get_user(user_id)
            user.custom_templates.append(template)
            self.set_user(user)
        except Exception:
            raise

    def delete_custom_template(self, user_id: int, template_title: str) -> None:
        if not self.user_is_exist(user_id):
            raise ValueError("User not found")

        try:
            user = self.get_user(user_id)
            user.custom_templates = [
                template
                for template in user.custom_templates
                if template.title != template_title
            ]
            self.set_user(user)
        except Exception:
            raise

    def set_least_template(self, user_id: int, template: Template) -> None:
        if not self.user_is_exist(user_id):
            raise ValueError("User not found")

        try:
            user = self.get_user(user_id)
            user.least_template = template
            self.set_user(user)
        except Exception:
            raise


if __name__ == "__main__":
    pass
