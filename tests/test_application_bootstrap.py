from __future__ import annotations

from bootstrap.testing import InMemoryTemplateRepository, create_test_application
from presentation.discord.client import BotClient
from presentation.discord.services import DiscordCommandUseCases


def test_build_discord_application_uses_di_container() -> None:
    repository = InMemoryTemplateRepository()

    bundle = create_test_application(repository_factory=lambda _: repository)

    client = bundle.application.client

    assert isinstance(client, BotClient)
    assert client.db is repository
    assert client.command_usecases.template_service._repository is repository  # type: ignore[attr-defined]

    resolved_client = bundle.context.injector.get(BotClient)
    assert resolved_client is client

    usecases = bundle.context.injector.get(DiscordCommandUseCases)
    assert usecases is client.command_usecases

    command_names = {command.name for command in client.tree.get_commands()}
    assert {"ping", "amidakuji"}.issubset(command_names)

    assert bundle.context.config.discord.token == "test-token"
