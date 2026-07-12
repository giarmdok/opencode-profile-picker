"""Main Textual application for oopps."""

from __future__ import annotations

from textual.app import App

from opencode_profile_picker.config.discover import DiscoveryResult
from opencode_profile_picker.profiles.store import ProfileStoreManager
from opencode_profile_picker.tui.screens.confirm_delete import ConfirmDeleteScreen
from opencode_profile_picker.tui.screens.keyset_edit import KeySetEditScreen
from opencode_profile_picker.tui.screens.keyset_list import KeySetListScreen
from opencode_profile_picker.tui.screens.launch import LaunchScreen
from opencode_profile_picker.tui.screens.main import MainScreen
from opencode_profile_picker.tui.screens.profile_edit import ProfileEditScreen
from opencode_profile_picker.tui.screens.reset_confirm import ResetConfirmScreen
from opencode_profile_picker.tui.screens.unlock import UnlockScreen


class OoppsApp(App[None]):
    """The oopps profile picker TUI application."""

    SCREENS = {
        "unlock": UnlockScreen,
        "reset_confirm": ResetConfirmScreen,
        "main": MainScreen,
        "profile_edit": ProfileEditScreen,
        "keyset_list": KeySetListScreen,
        "keyset_edit": KeySetEditScreen,
        "confirm_delete": ConfirmDeleteScreen,
        "launch": LaunchScreen,
    }

    CSS = """
    Screen {
        background: $surface;
    }

    .hidden {
        display: none;
    }

    .section-title {
        text-style: bold;
        padding-bottom: 1;
    }

    .empty-message {
        color: $text-muted;
        text-align: center;
        padding: 2;
    }

    .warning {
        color: $warning;
    }

    .error {
        color: $error;
    }

    .success {
        color: $success;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.store_manager: ProfileStoreManager | None = None
        self.discovery: DiscoveryResult | None = None

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "oopps"
        self.push_screen("unlock", self._on_unlock_done)

    def _on_unlock_done(self, _result: object) -> None:
        """Called after unlock screen is dismissed."""
        self.push_screen("main")
