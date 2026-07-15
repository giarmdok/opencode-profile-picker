"""Edit key value modal screen."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label


class EditKeyValueModal(ModalScreen[str | None]):
    """Modal screen for editing a key's value."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    CSS = """
    #edit-key-container {
        width: 100%;
        max-width: 50;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }

    #edit-key-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #edit-key-context {
        padding-bottom: 1;
        color: $text-muted;
    }

    #edit-key-buttons {
        padding-top: 1;
        align: center middle;
    }
    """

    def __init__(
        self,
        provider: str,
        env_var: str,
        current_value: str | None = None,
    ) -> None:
        super().__init__()
        self._provider = provider
        self._env_var = env_var
        self._current_value = current_value

    def compose(self) -> ComposeResult:
        with Container(id="edit-key-container"):
            yield Label(f"Edit: {self._env_var}", id="edit-key-title")
            yield Label(
                f"Provider: {self._provider or '(none)'}\nEnv Var: {self._env_var}",
                id="edit-key-context",
            )
            yield Input(
                value=self._current_value or "",
                placeholder="sk-...",
                password=True,
                id="value-input",
            )
            with Horizontal(id="edit-key-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
        yield Footer()

    @on(Button.Pressed, "#save-btn")
    def handle_save(self) -> None:
        try:
            value_input = self.query_one("#value-input", Input)
        except Exception:
            self.dismiss(None)
            return
        self.dismiss(value_input.value.strip())

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        """Save via keyboard shortcut."""
        self.handle_save()
