from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

import firebase_admin
from firebase_admin import App, credentials, firestore

from db.constants import COLLECTION_SENTINEL_DOCUMENT_ID, REQUIRED_COLLECTIONS
from db.repositories import (
    HistoryRepository,
    InfoRepository,
    SharedTemplateRepository,
    UserRepository,
)
from db.serializers import (
    deserialize_assignment_history,
    deserialize_template,
    normalize_template_for_user,
    serialize_template,
)

from domain import (
    AssignmentHistory,
    ResultEmbedMode,
    SelectionMode,
    Template,
    TemplateScope,
    UserInfo,
)
from domain.interfaces.repositories import TemplateRepository
from domain.services.selection_mode_service import coerce_selection_mode
from domain.services.template_service import merge_templates

__all__ = [
    "DBManager",
    "COLLECTION_SENTINEL_DOCUMENT_ID",
    "REQUIRED_COLLECTIONS",
    "UserRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "HistoryRepository",
]


class DBManager(TemplateRepository):
    """Firestore上のデータを操作する高水準マネージャ。"""

    _global_instance: ClassVar["DBManager | None"] = None

    def __init__(self) -> None:
        self._app: App | None = None
        self.db: firestore.firestore.Client | None = None
        self.user_repository: UserRepository | None = None
        self.info_repository: InfoRepository | None = None
        self.shared_template_repository: SharedTemplateRepository | None = None
        self.history_repository: HistoryRepository | None = None

    @classmethod
    def get_instance(cls) -> "DBManager":
        if cls._global_instance is None:
            cls._global_instance = cls()
        return cls._global_instance

    @classmethod
    def set_global_instance(cls, instance: "DBManager" | None) -> None:
        cls._global_instance = instance

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
        client = firestore.client(app=app)
        self._attach_client(client)

    def with_client(self, client: firestore.firestore.Client) -> None:
        if self.db is not None and self.db is not client:
            raise RuntimeError(
                "DBManager is already initialized with a different Firestore client"
            )
        self._attach_client(client)

    def _attach_client(self, client: firestore.firestore.Client) -> None:
        self.db = client
        self.user_repository = UserRepository(client)
        self.info_repository = InfoRepository(client)
        self.shared_template_repository = SharedTemplateRepository(client)
        self.history_repository = HistoryRepository(client)
        self.ensure_required_collections()

    @property
    def is_configured(self) -> bool:
        return all(
            (
                self.db,
                self.user_repository,
                self.info_repository,
                self.history_repository,
            )
        )

    def ensure_required_collections(self) -> None:
        if self.db is None:
            raise RuntimeError(
                "DBManager is not configured. Call initialize() or with_app() before use."
            )

        sentinel_payload = {
            "_system": True,
            "_purpose": "collection_sentinel",
            "created_at": datetime.now(timezone.utc),
        }

        for collection_name in REQUIRED_COLLECTIONS:
            collection_ref = self.db.collection(collection_name)
            document_ref = collection_ref.document(COLLECTION_SENTINEL_DOCUMENT_ID)
            snapshot = document_ref.get()
            if not getattr(snapshot, "exists", False):
                document_ref.set(sentinel_payload)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
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

    def _get_shared_template_repository(self) -> SharedTemplateRepository:
        self._ensure_configured()
        assert self.shared_template_repository is not None
        return self.shared_template_repository

    @staticmethod
    def _merge_template_lists(*template_lists: Iterable[Template]) -> list[Template]:
        return merge_templates(*template_lists)

    @staticmethod
    def _coerce_selection_mode(value: SelectionMode | str) -> SelectionMode:
        return coerce_selection_mode(value)

    @staticmethod
    def _coerce_embed_mode(value: ResultEmbedMode | str) -> ResultEmbedMode:
        if isinstance(value, ResultEmbedMode):
            return value
        normalized = str(value).lower()
        try:
            return ResultEmbedMode(normalized)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError("Invalid embed mode") from exc

    def _get_history_repository(self) -> HistoryRepository:
        self._ensure_configured()
        assert self.history_repository is not None
        return self.history_repository

    def _validate_user(self, data: dict) -> bool:
        return data["id"] is not None and data["name"] is not None

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
                scope=TemplateScope.PUBLIC,
            ),
            Template(
                title="Valorant",
                choices=["Duelist", "Initiator", "Controller", "Sentinel"],
                scope=TemplateScope.PUBLIC,
            ),
        ]
        default_templates = [
            serialize_template(template) for template in default_templates
        ]
        default_templates = {"default_templates": default_templates}
        info_repository.create_document("default_templates", default_templates)

    def ensure_default_templates(self) -> list[Template]:
        """既定のテンプレートを初期化し、一覧を返す。"""

        return self.get_default_templates()

    def get_default_templates(self) -> list[Template]:
        info_repository = self._get_info_repository()
        templates = info_repository.read_document("default_templates")
        if not isinstance(templates, dict) or "default_templates" not in templates:
            self._init_default_templates()
            templates = info_repository.read_document("default_templates")

        template_items = (
            templates.get("default_templates") if isinstance(templates, dict) else None
        )
        if not isinstance(template_items, list):
            raise ValueError("Invalid default template data")

        deserialized: list[Template] = []
        for item in template_items:
            if not isinstance(item, dict):
                raise ValueError("Invalid default template data")
            deserialized.append(deserialize_template(item))
        return deserialized

    def list_shared_templates(
        self,
        *,
        scope: TemplateScope | None = None,
        guild_id: int | None = None,
        created_by: int | None = None,
    ) -> list[Template]:
        repository = self._get_shared_template_repository()
        query_kwargs: dict[str, object | None] = {
            "scope": scope.value if scope else None,
            "guild_id": guild_id,
        }
        if created_by is not None:
            query_kwargs["created_by"] = created_by

        raw_templates = repository.list_templates(**query_kwargs)
        templates: list[Template] = []
        for item in raw_templates:
            if not hasattr(item, "to_dict"):
                continue
            data = item.to_dict()
            if not isinstance(data, dict):
                continue
            data.setdefault("template_id", getattr(item, "id", None))
            if scope is not None:
                data.setdefault("scope", scope.value)
            try:
                templates.append(deserialize_template(data))
            except ValueError:
                continue
        return templates

    def get_shared_templates_for_user(
        self, *, guild_id: int | None
    ) -> tuple[list[Template], list[Template]]:
        guild_templates: list[Template] = []
        if guild_id is not None:
            guild_templates = self.list_shared_templates(
                scope=TemplateScope.GUILD, guild_id=guild_id
            )
        public_templates = self.list_shared_templates(scope=TemplateScope.PUBLIC)
        return guild_templates, public_templates

    def _read_or_initialize_selection_mode(
        self, info_repository: InfoRepository
    ) -> tuple[dict[str, str], bool]:
        data = info_repository.read_document("selection_mode")
        should_initialize = not isinstance(data, dict) or "selection_mode" not in data
        if should_initialize:
            data = {"selection_mode": SelectionMode.RANDOM.value}
            info_repository.create_document("selection_mode", data)
        return data, should_initialize

    def toggle_embed_mode(self) -> None:
        info_repository = self._get_info_repository()
        data, _ = self._read_or_initialize_embed_mode(info_repository)
        if data["embed_mode"] == "compact":
            data["embed_mode"] = "detailed"
        else:
            data["embed_mode"] = "compact"
        info_repository.create_document("embed_mode", data)

    def get_embed_mode(self) -> str:
        info_repository = self._get_info_repository()
        data, _ = self._read_or_initialize_embed_mode(info_repository)
        return data["embed_mode"]

    def set_embed_mode(self, mode: ResultEmbedMode | str) -> None:
        embed_mode = self._coerce_embed_mode(mode)
        info_repository = self._get_info_repository()
        data, _ = self._read_or_initialize_embed_mode(info_repository)
        data["embed_mode"] = embed_mode.value
        info_repository.create_document("embed_mode", data)

    def set_selection_mode(self, mode: SelectionMode | str) -> None:
        selection_mode = self._coerce_selection_mode(mode)
        info_repository = self._get_info_repository()
        data, _ = self._read_or_initialize_selection_mode(info_repository)
        data["selection_mode"] = selection_mode.value
        info_repository.create_document("selection_mode", data)

    def get_selection_mode(self) -> str:
        info_repository = self._get_info_repository()
        data, _ = self._read_or_initialize_selection_mode(info_repository)
        return data["selection_mode"]

    def save_history(
        self,
        *,
        guild_id: int,
        template: Template,
        pairs: "PairList",
        selection_mode: SelectionMode | str,
    ) -> None:
        history_repository = self._get_history_repository()
        mode_enum = self._coerce_selection_mode(selection_mode)
        timestamp = datetime.now(timezone.utc)
        entries = [
            {
                "user_id": pair.user.id,
                "user_name": getattr(pair.user, "display_name", pair.user.name),
                "choice": pair.choice,
            }
            for pair in pairs.pairs
        ]
        data = {
            "guild_id": guild_id,
            "template_title": template.title,
            "choices": list(template.choices),
            "selection_mode": mode_enum.value,
            "created_at": timestamp,
            "entries": entries,
        }
        history_repository.add_entry(data)

    def get_recent_history(
        self,
        *,
        guild_id: int,
        template_title: str | None = None,
        limit: int = 10,
        since: datetime | None = None,
    ) -> list[AssignmentHistory]:
        history_repository = self._get_history_repository()
        try:
            documents = history_repository.fetch_recent(
                guild_id=guild_id, template_title=template_title, limit=limit, since=since
            )
        except Exception:
            raise

        if not documents:
            return []

        histories: list[AssignmentHistory] = []
        for document in documents:
            if not isinstance(document, dict):
                continue
            try:
                histories.append(deserialize_assignment_history(document))
            except ValueError:
                continue
        return histories

    def init_user(self, user_id: int, name: str) -> None:
        user_repository = self._get_user_repository()
        default_templates = self.get_default_templates()
        default_templates = [
            serialize_template(template) for template in default_templates
        ]

        data = {
            "name": name,
            "id": user_id,
            "least_template": None,
            "custom_templates": default_templates,
        }
        user_repository.create_document(user_id, data)

    # これいる？
    def set_user(self, user: UserInfo) -> None:
        user_repository = self._get_user_repository()
        least_template = (
            serialize_template(user.least_template)
            if user.least_template is not None
            else None
        )
        custom_templates = [
            serialize_template(template) for template in user.custom_templates
        ]
        data = {
            "name": user.name,
            "id": user.id,
            "least_template": least_template,
            "custom_templates": custom_templates,
        }
        user_repository.create_document(user.id, data)

    def get_user(
        self,
        user_id: int,
        *,
        guild_id: int | None = None,
        include_shared: bool = True,
    ) -> UserInfo | None:
        user_repository = self._get_user_repository()
        data = user_repository.read_document(user_id)
        if data is None:
            return None

        least_template = None
        if data.get("least_template"):
            least_payload = data["least_template"]
            if not isinstance(least_payload, dict):
                raise ValueError("Invalid template data")
            least_template = deserialize_template(least_payload)

        custom_templates: list[Template] = []
        for template_data in data.get("custom_templates") or []:
            if not isinstance(template_data, dict):
                raise ValueError("Invalid template data")
            custom_templates.append(deserialize_template(template_data))

        shared_templates: list[Template] = []
        public_templates: list[Template] = []
        if include_shared:
            guild_templates, public_shared = self.get_shared_templates_for_user(
                guild_id=guild_id
            )
            default_templates = self.get_default_templates()
            shared_templates = guild_templates
            public_templates = self._merge_template_lists(
                public_shared,
                default_templates,
            )

        return UserInfo(
            id=data["id"],
            name=data["name"],
            least_template=least_template,
            custom_templates=custom_templates,
            shared_templates=shared_templates,
            public_templates=public_templates,
        )

    def delete_user(self, user_id: int) -> None:
        user_repository = self._get_user_repository()
        user_repository.delete_document(user_id)

    def user_is_exist(self, user_id: int) -> bool:
        try:
            repository = self._get_user_repository()
        except Exception:
            return False

        try:
            return repository.read_document(user_id) is not None
        except Exception:
            return False

    def add_custom_template(self, user_id: int, template: Template) -> None:
        user = self.get_user(user_id, include_shared=False)
        if user is None:
            raise ValueError("User not found")
        updated_template = normalize_template_for_user(template, user_id)
        user.custom_templates.append(updated_template)
        self.set_user(user)

    def update_custom_template(self, user_id: int, template: Template) -> None:
        if not template.template_id:
            raise ValueError("Template id is required")

        user = self.get_user(user_id, include_shared=False)
        if user is None:
            raise ValueError("User not found")

        sanitized = replace(
            template,
            scope=TemplateScope.PRIVATE,
            created_by=user_id,
            guild_id=None,
        )

        for index, existing in enumerate(user.custom_templates):
            if existing.template_id == sanitized.template_id:
                user.custom_templates[index] = sanitized
                break
        else:
            raise ValueError("Template not found")

        self.set_user(user)

    def delete_custom_template(
        self,
        user_id: int,
        *,
        template_id: str | None = None,
        template_title: str | None = None,
    ) -> None:
        user = self.get_user(user_id, include_shared=False)
        if user is None:
            raise ValueError("User not found")
        if template_id is None and template_title is None:
            raise ValueError("Template identifier is required")

        def should_keep(template: Template) -> bool:
            if template_id is not None and template.template_id == template_id:
                return False
            if template_title is not None and template.title == template_title:
                return False
            return True

        user.custom_templates = [
            template for template in user.custom_templates if should_keep(template)
        ]
        self.set_user(user)

    def set_least_template(self, user_id: int, template: Template) -> None:
        user = self.get_user(user_id, include_shared=False)
        if user is None:
            raise ValueError("User not found")
        user.least_template = template
        self.set_user(user)

    def create_shared_template(self, template: Template) -> Template:
        if template.scope not in (TemplateScope.GUILD, TemplateScope.PUBLIC):
            raise ValueError("Shared templates must have a guild or public scope")
        repository = self._get_shared_template_repository()
        data = serialize_template(template)
        template_id = repository.add_template(data)
        return replace(template, template_id=template_id)

    def delete_shared_template(self, template_id: str) -> None:
        repository = self._get_shared_template_repository()
        repository.delete_template(template_id)

    def copy_shared_template_to_user(self, user_id: int, template: Template) -> Template:
        if template.scope == TemplateScope.PRIVATE:
            raise ValueError("Cannot copy private template as shared")
        user = self.get_user(user_id, include_shared=False)
        if user is None:
            raise ValueError("User not found")

        existing_titles = {t.title for t in user.custom_templates}
        base_title = template.title
        new_title = base_title
        counter = 1
        while new_title in existing_titles:
            counter += 1
            new_title = f"{base_title} ({counter})"

        template_with_title = replace(template, title=new_title)
        new_template = normalize_template_for_user(template_with_title, user_id)
        user.custom_templates.append(new_template)
        self.set_user(user)
        return new_template


if __name__ == "__main__":
    pass
