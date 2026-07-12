"""Key set edit screen — add, edit, remove keys."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Label, Select, Static

from opencode_profile_picker.config.discover import PROVIDER_KEY_MAP
from opencode_profile_picker.profiles.models import KeySet
from opencode_profile_picker.profiles.operations import (
    add_key,
    add_key_set,
)


class KeySetEditScreen(Screen[None]):
    """Screen for editing keys within a key set."""

    CSS = """
    #keyset-edit-container {
        width: 70;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
    }

    #keyset-edit-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #keyset-edit-error {
        color: $error;
        padding-top: 1;
    }

    #keyset-edit-buttons {
        padding-top: 1;
        align: center middle;
    }

    #add-key-form {
        padding: 1 0;
        border: solid $surface-darken-1;
        margin: 1 0;
    }

    .form-row {
        padding: 0 1;
    }
    """

    def __init__(self, keyset_name: str | None = None) -> None:
        super().__init__()
        self._keyset_name = keyset_name
        self._is_new = keyset_name is None

    def compose(self) -> ComposeResult:
        title = "New Key Set" if self._is_new else f"Edit: {self._keyset_name}"

        provider_options = [(f"{k} ({v})", k) for k, v in sorted(PROVIDER_KEY_MAP.items())]
        provider_options.append(("Custom...", "__custom__"))

        with Container(id="keyset-edit-container"):
            yield Label(title, id="keyset-edit-title")

            if self._is_new:
                with Container(classes="form-row"):
                    yield Label("Key Set Name:")
                    yield Input(placeholder="my-keys", id="name-input")

            yield DataTable(id="keys-table")

            with Container(id="add-key-form"):
                yield Label("Add Key:", classes="section-title")
                with Container(classes="form-row"):
                    yield Label("Provider:")
                    yield Select(provider_options, id="provider-select")
                with Container(classes="form-row"):
                    yield Label("Env Var:")
                    yield Input(placeholder="OPENAI_API_KEY", id="env-var-input")
                with Container(classes="form-row"):
                    yield Label("Value (leave empty for env fallback):")
                    yield Input(placeholder="sk-...", id="value-input", password=True)
                with Horizontal(id="keyset-edit-buttons"):
                    yield Button("Add Key", variant="primary", id="add-key-btn")

            yield Static("", id="keyset-edit-error")

            with Horizontal(id="keyset-edit-buttons"):
                yield Button("Save & Back", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        table = self.query_one("#keys-table", DataTable)
        table.add_columns("Provider", "Env Var", "Value")
        table.cursor_type = "row"
        self._refresh_table()

    def _get_keyset(self) -> KeySet | None:
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return None
        if self._is_new:
            return None
        return manager.store.key_sets.get(self._keyset_name or "")

    def _refresh_table(self) -> None:
        table = self.query_one("#keys-table", DataTable)
        table.clear()
        ks = self._get_keyset()
        if ks:
            for entry in ks.keys.values():
                display_value = "••••••" if entry.value else "(env)"
                table.add_row(entry.provider, entry.env_var, display_value, key=entry.env_var)

    @on(Select.Changed, "#provider-select")
    def _on_provider_changed(self, event: Select.Changed) -> None:
        """Auto-fill env var when provider is selected."""
        provider = str(event.value) if event.value else ""
        if provider and provider != "__custom__":
            env_var = PROVIDER_KEY_MAP.get(provider, "")
            if env_var:
                try:
                    env_input = self.query_one("#env-var-input", Input)
                    env_input.value = env_var
                except Exception:
                    pass

    @on(Button.Pressed, "#add-key-btn")
    def handle_add_key(self) -> None:
        """Add a key to the key set."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return

        # If new key set, create it first
        if self._is_new:
            try:
                name_input = self.query_one("#name-input", Input)
                name = name_input.value.strip()
            except Exception:
                return
            if not name:
                self._show_error("Key set name is required")
                return
            try:
                add_key_set(manager.store, name)
                self._keyset_name = name
                self._is_new = False
                manager.save()
            except ValueError as e:
                self._show_error(str(e))
                return

        ks = self._get_keyset()
        if ks is None:
            return

        try:
            provider_select = self.query_one("#provider-select", Select)
            env_input = self.query_one("#env-var-input", Input)
            value_input = self.query_one("#value-input", Input)
        except Exception:
            return

        provider = str(provider_select.value) if provider_select.value else ""
        env_var = env_input.value.strip()
        value = value_input.value.strip() or None

        if not env_var:
            self._show_error("Environment variable name is required")
            return

        try:
            add_key(ks, provider, env_var, value)
            manager.save()
            self._refresh_table()
            # Clear inputs
            env_input.value = ""
            value_input.value = ""
        except ValueError as e:
            self._show_error(str(e))

    @on(Button.Pressed, "#save-btn")
    def handle_save(self) -> None:
        self.dismiss()

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        self.dismiss()

    def _show_error(self, message: str) -> None:
        try:
            error_widget = self.query_one("#keyset-edit-error", Static)
            error_widget.update(message)
        except Exception:
            pass
