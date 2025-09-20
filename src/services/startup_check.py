from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List

import discord

from db_manager import DBManager
from utils import ERROR, INFO, SUCCESS, WARN, green, red, yellow


class CheckStatus(Enum):
    """Represents the outcome of a startup self-check."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class CheckResult:
    """Detailed result for a single self-check item."""

    name: str
    status: CheckStatus
    message: str


class StartupSelfCheck:
    """Run diagnostics required for safe bot execution."""

    REQUIRED_COLLECTIONS: tuple[str, ...] = (
        "users",
        "info",
        "shared_templates",
        "history",
    )

    def __init__(self, db_manager: DBManager) -> None:
        self._db_manager = db_manager

    def run(self, *, discord_client: discord.Client) -> bool:
        """Execute all self-checks and log their results."""

        logging.info(INFO + "Running startup self-checks...")
        results: List[CheckResult] = []

        results.append(self._check_discord(discord_client))
        results.append(self._check_firebase())
        results.extend(self._check_collections(self.REQUIRED_COLLECTIONS))

        for result in results:
            if result.status is CheckStatus.OK:
                logging.info(
                    INFO
                    + SUCCESS
                    + f"[{result.name}] {green(result.message)}"
                )
            elif result.status is CheckStatus.WARNING:
                logging.warning(
                    WARN
                    + f"[{result.name}] {yellow(result.message)}"
                )
            else:
                logging.error(
                    ERROR
                    + f"[{result.name}] {red(result.message)}"
                )

        has_error = any(result.status is CheckStatus.ERROR for result in results)
        if has_error:
            logging.error(ERROR + "Startup self-check failed.")
        else:
            logging.info(INFO + SUCCESS + "Startup self-check completed without errors.")

        return not has_error

    def _check_discord(self, discord_client: discord.Client) -> CheckResult:
        """Verify that the Discord client authenticated successfully."""

        user = getattr(discord_client, "user", None)
        if user is None:
            return CheckResult(
                name="discord_auth",
                status=CheckStatus.ERROR,
                message="Discord client user is not available. Authentication may have failed.",
            )

        return CheckResult(
            name="discord_auth",
            status=CheckStatus.OK,
            message=f"Authenticated as {user} (id={user.id}).",
        )

    def _check_firebase(self) -> CheckResult:
        """Confirm that the Firebase client is initialized and reachable."""

        db = getattr(self._db_manager, "db", None)
        if db is None:
            return CheckResult(
                name="firebase_auth",
                status=CheckStatus.ERROR,
                message="Firestore client is not initialized.",
            )

        try:
            project_id = getattr(db, "project", "<unknown>")
            next(db.collections(), None)
        except Exception as exc:  # pragma: no cover - defensive logging
            return CheckResult(
                name="firebase_auth",
                status=CheckStatus.ERROR,
                message=f"Failed to connect to Firestore: {exc}",
            )

        return CheckResult(
            name="firebase_auth",
            status=CheckStatus.OK,
            message=f"Connected to Firestore project '{project_id}'.",
        )

    def _check_collections(self, collections: Iterable[str]) -> list[CheckResult]:
        """Inspect required Firestore collections and ensure they are reachable."""

        db = getattr(self._db_manager, "db", None)
        if db is None:
            return [
                CheckResult(
                    name="firestore_collections",
                    status=CheckStatus.ERROR,
                    message="Firestore client is not initialized.",
                )
            ]

        results: list[CheckResult] = []
        for collection_name in collections:
            try:
                has_document = next(
                    db.collection(collection_name).limit(1).stream(),
                    None,
                )
                if has_document is None:
                    results.append(
                        CheckResult(
                            name=f"collection:{collection_name}",
                            status=CheckStatus.WARNING,
                            message="No documents found. Collection is accessible but currently empty.",
                        )
                    )
                else:
                    results.append(
                        CheckResult(
                            name=f"collection:{collection_name}",
                            status=CheckStatus.OK,
                            message="Collection is accessible and contains documents.",
                        )
                    )
            except Exception as exc:  # pragma: no cover - defensive logging
                results.append(
                    CheckResult(
                        name=f"collection:{collection_name}",
                        status=CheckStatus.ERROR,
                        message=f"Failed to access collection: {exc}",
                    )
                )

        return results
