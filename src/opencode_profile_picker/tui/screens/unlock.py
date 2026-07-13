"""Unlock screen — master password entry and first-run setup."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from opencode_profile_picker.profiles.store import ProfileStoreManager


class UnlockScreen(Screen[None]):
    """Screen for entering the master password or creating one on first run."""

    BINDINGS = [
        ("escape", "quit", "Quit"),
    ]

    CSS = """
    #unlock-container {
        width: 100%;
        max-width: 50;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
    }

    #unlock-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #unlock-error {
        color: $error;
        text-align: center;
        padding-top: 1;
    }

    #unlock-hint {
        color: $text-muted;
        text-align: center;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the unlock UI."""
        is_first_run = not ProfileStoreManager.store_exists()

        with Container(id="unlock-container"):
            if is_first_run:
                yield Label("Create Master Password", id="unlock-title")
                yield Label(
                    "This password encrypts your API keys on disk.\n"
                    "You will need it each time you run oopps.",
                    id="unlock-hint",
                )
                yield Input(
                    placeholder="Enter master password",
                    password=True,
                    id="password-input",
                )
                yield Input(
                    placeholder="Confirm master password",
                    password=True,
                    id="confirm-input",
                )
                yield Button("Create", variant="primary", id="unlock-btn")
            else:
                yield Label("Unlock oopps", id="unlock-title")
                yield Input(
                    placeholder="Enter master password",
                    password=True,
                    id="password-input",
                )
                yield Button("Unlock", variant="primary", id="unlock-btn")
                yield Button("Forgot Password?", variant="error", id="forgot-btn")

            yield Static("", id="unlock-error")

    @on(Button.Pressed, "#unlock-btn")
    def handle_unlock(self) -> None:
        """Handle the unlock/create button press."""
        self._do_unlock()

    @on(Input.Submitted, "#password-input")
    def handle_password_submit(self) -> None:
        """Handle Enter key on password input."""
        self._do_unlock()

    @on(Input.Submitted, "#confirm-input")
    def handle_confirm_submit(self) -> None:
        """Handle Enter key on confirm password input."""
        self._do_unlock()

    def _do_unlock(self) -> None:
        """Perform the unlock/create action."""
        password = self.query_one("#password-input", Input).value

        if not password:
            self._show_error("Password cannot be empty")
            return

        is_first_run = not ProfileStoreManager.store_exists()

        if is_first_run:
            confirm = self.query_one("#confirm-input", Input).value
            if password != confirm:
                self._show_error("Passwords do not match")
                return
            if len(password) < 8:
                self._show_error("Password should be at least 8 characters")
                return
            try:
                manager = ProfileStoreManager.create(password)
                self._on_success(manager)
            except Exception as e:
                self._show_error(f"Failed to create store: {e}")
        else:
            try:
                manager = ProfileStoreManager.load(password)
                self._on_success(manager)
            except FileNotFoundError:
                self._show_error("Store file not found")
            except ValueError:
                self._show_error("Incorrect password")

    @on(Button.Pressed, "#forgot-btn")
    def handle_forgot(self) -> None:
        """Handle the forgot password button."""
        self.app.push_screen("reset_confirm", self._on_reset_result)

    def _on_reset_result(self, reset: bool | None) -> None:
        """Handle the result from the reset confirmation screen."""
        if reset:
            # Delete the store file
            import contextlib

            with contextlib.suppress(Exception):
                ProfileStoreManager._get_store_path().unlink(missing_ok=True)
            self.app.pop_screen()
            self.app.push_screen(UnlockScreen())

    def _on_success(self, manager: ProfileStoreManager) -> None:
        """Called when unlock/create succeeds."""
        app = self.app
        if hasattr(app, "store_manager"):
            app.store_manager = manager
        self.dismiss()

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        error_widget = self.query_one("#unlock-error", Static)
        error_widget.update(message)
