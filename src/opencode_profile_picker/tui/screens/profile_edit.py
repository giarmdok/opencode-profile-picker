"""Profile edit screen — create or edit a profile."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from opencode_profile_picker.profiles.operations import add_profile, update_profile


class ProfileEditScreen(Screen[None]):
    """Screen for creating or editing a profile."""

    CSS = """
    #edit-container {
        width: 60;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
    }

    #edit-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    .edit-field {
        padding: 1 0;
    }

    .edit-label {
        padding-bottom: 1;
    }

    #compat-info {
        padding: 1 0;
        color: $text-muted;
    }

    #edit-error {
        color: $error;
        padding-top: 1;
    }

    #edit-buttons {
        padding-top: 1;
        align: center middle;
    }
    """

    def __init__(self, profile_name: str | None = None) -> None:
        super().__init__()
        self._profile_name = profile_name
        self._is_new = profile_name is None

    def compose(self) -> ComposeResult:
        app = self.app
        manager = getattr(app, "store_manager", None)
        discovery = getattr(app, "discovery", None)

        preset_options: list[tuple[str, str]] = []
        if discovery and discovery.presets:
            preset_options = [(name, name) for name in sorted(discovery.presets.keys())]

        keyset_options: list[tuple[str, str]] = []
        if manager:
            keyset_options = [(name, name) for name in sorted(manager.store.key_sets.keys())]

        with Container(id="edit-container"):
            if self._is_new:
                yield Label("New Profile", id="edit-title")
            else:
                yield Label(f"Edit Profile: {self._profile_name}", id="edit-title")

            if self._is_new:
                with Container(classes="edit-field"):
                    yield Label("Name:", classes="edit-label")
                    yield Input(placeholder="profile-name", id="name-input")

            with Container(classes="edit-field"):
                yield Label("Preset:", classes="edit-label")
                if preset_options:
                    yield Select(preset_options, id="preset-select")
                else:
                    yield Label("No presets discovered", classes="warning")

            with Container(classes="edit-field"):
                yield Label("Key Set:", classes="edit-label")
                if keyset_options:
                    yield Select(keyset_options, id="keyset-select")
                else:
                    yield Label("No key sets available", classes="warning")

            yield Static("", id="compat-info")
            yield Static("", id="edit-error")

            with Horizontal(id="edit-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        """Pre-populate fields if editing."""
        if not self._is_new and self._profile_name:
            app = self.app
            manager = getattr(app, "store_manager", None)
            if manager and self._profile_name in manager.store.profiles:
                profile = manager.store.profiles[self._profile_name]
                try:
                    preset_select = self.query_one("#preset-select", Select)
                    preset_select.value = profile.preset
                except Exception:
                    pass
                try:
                    keyset_select = self.query_one("#keyset-select", Select)
                    keyset_select.value = profile.key_set
                except Exception:
                    pass

    @on(Select.Changed)
    def _on_select_changed(self) -> None:
        """Update compatibility info when selections change."""
        self._update_compat()

    def _update_compat(self) -> None:
        """Show which keys the preset needs and whether the key set provides them."""
        compat = self.query_one("#compat-info", Static)
        app = self.app
        manager = getattr(app, "store_manager", None)
        discovery = getattr(app, "discovery", None)

        if not manager or not discovery:
            compat.update("")
            return

        try:
            preset_select = self.query_one("#preset-select", Select)
            keyset_select = self.query_one("#keyset-select", Select)
        except Exception:
            return

        preset_name = str(preset_select.value) if preset_select.value else ""
        keyset_name = str(keyset_select.value) if keyset_select.value else ""

        if not preset_name or not keyset_name:
            compat.update("")
            return

        required = discovery.presets.get(preset_name, set())
        keyset = manager.store.key_sets.get(keyset_name)

        lines = [f"Preset '{preset_name}' requires:"]
        for key in sorted(required):
            if key.startswith("UNKNOWN:"):
                lines.append(f"  ? {key} (unknown provider)")
            elif keyset and key in keyset.keys:
                entry = keyset.keys[key]
                if entry.value:
                    lines.append(f"  ✓ {key} (stored)")
                else:
                    lines.append(f"  ~ {key} (env fallback)")
            else:
                lines.append(f"  ✗ {key} (missing)")

        compat.update("\n".join(lines))

    @on(Button.Pressed, "#save-btn")
    def handle_save(self) -> None:
        """Save the profile."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return

        # Get name
        if self._is_new:
            try:
                name_input = self.query_one("#name-input", Input)
                name = name_input.value.strip()
            except Exception:
                return
            if not name:
                self._show_error("Name is required")
                return
        else:
            name = self._profile_name or ""

        # Get preset and key set
        try:
            preset_select = self.query_one("#preset-select", Select)
            keyset_select = self.query_one("#keyset-select", Select)
        except Exception:
            return

        preset = str(preset_select.value) if preset_select.value else ""
        keyset = str(keyset_select.value) if keyset_select.value else ""

        if not preset:
            self._show_error("Preset is required")
            return
        if not keyset:
            self._show_error("Key set is required")
            return

        try:
            if self._is_new:
                add_profile(manager.store, name, preset, keyset)
            else:
                update_profile(manager.store, name, preset=preset, key_set=keyset)
            manager.save()
            self.dismiss()
        except ValueError as e:
            self._show_error(str(e))

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.dismiss()

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        try:
            error_widget = self.query_one("#edit-error", Static)
            error_widget.update(message)
        except Exception:
            pass
