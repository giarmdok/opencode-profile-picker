"""Reset confirmation screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label


class ResetConfirmScreen(ModalScreen[bool]):
    """Modal screen confirming password reset with data loss warning."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    #reset-container {
        width: 100%;
        max-width: 50;
        height: auto;
        align: center middle;
        border: solid $error;
        padding: 1 2;
        background: $surface;
    }

    #reset-title {
        text-align: center;
        text-style: bold;
        color: $error;
        padding-bottom: 1;
    }

    #reset-warning {
        text-align: center;
        padding-bottom: 1;
    }

    #reset-buttons {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="reset-container"):
            yield Label("Reset Master Password", id="reset-title")
            yield Label(
                "All stored API keys will be permanently lost.\n"
                "You will need to re-enter them after creating a new password.",
                id="reset-warning",
            )
            with Container(id="reset-buttons"):
                yield Button("Reset (lose all keys)", variant="error", id="reset-btn")
                yield Button("Cancel", variant="primary", id="cancel-btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reset-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel the dialog via keyboard."""
        self.dismiss(False)
