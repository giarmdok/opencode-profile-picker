"""Confirm delete modal screen."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal screen confirming a delete action."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("d", "delete", "Delete"),
    ]

    CSS = """
    #confirm-container {
        width: 100%;
        max-width: 50;
        height: auto;
        align: center middle;
        border: solid $error;
        padding: 1 2;
        background: $surface;
    }

    #confirm-title {
        text-align: center;
        text-style: bold;
        color: $error;
        padding-bottom: 1;
    }

    #confirm-message {
        text-align: center;
        padding-bottom: 1;
    }

    #confirm-buttons {
        align: center middle;
    }
    """

    def __init__(self, message: str | None = None) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="confirm-container"):
            yield Label("Confirm Delete", id="confirm-title")
            yield Label(
                self._message or "Are you sure you want to delete this?", id="confirm-message"
            )
            with Container(id="confirm-buttons"):
                yield Button("Delete", variant="error", id="delete-btn")
                yield Button("Cancel", variant="primary", id="cancel-btn")
        yield Footer()

    @on(Button.Pressed, "#delete-btn")
    def handle_delete(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel_button(self) -> None:
        self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel the dialog via keyboard."""
        self.dismiss(False)

    def action_delete(self) -> None:
        """Confirm delete via keyboard."""
        self.dismiss(True)
