"""Confirm delete modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal screen confirming a delete action."""

    CSS = """
    #confirm-container {
        width: 50;
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

    def compose(self) -> ComposeResult:
        with Container(id="confirm-container"):
            yield Label("Confirm Delete", id="confirm-title")
            yield Label("Are you sure you want to delete this?", id="confirm-message")
            with Container(id="confirm-buttons"):
                yield Button("Delete", variant="error", id="delete-btn")
                yield Button("Cancel", variant="primary", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)
