"""Key set edit screen — add, edit, remove keys."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Input, Label, Select, Static

from opencode_profile_picker.config.discover import PROVIDER_KEY_MAP
from opencode_profile_picker.profiles.models import KeySet
from opencode_profile_picker.profiles.operations import (
    add_key,
    add_key_set,
    compute_merge,
    remove_key,
    update_key_value,
)
from opencode_profile_picker.tui.screens.confirm_delete import ConfirmDeleteScreen
from opencode_profile_picker.tui.screens.edit_key_value_modal import EditKeyValueModal
from opencode_profile_picker.tui.screens.merge_import_modal import MergeImportModal


class KeySetEditScreen(Screen[None]):
    """Screen for editing keys within a key set."""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("enter", "edit_selected_key", "Edit"),
        ("e", "edit_selected_key", "Edit"),
        ("d", "delete_selected_key", "Delete"),
        ("delete", "delete_selected_key", "Delete"),
        ("a", "add_key", "Add Key"),
        ("i", "import_env", "Import"),
    ]

    CSS = """
    #keyset-edit-container {
        width: 100%;
        max-width: 70;
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
        provider_options.append(("──────────", ""))  # visual separator
        provider_options.append(("Custom env var...", "__custom__"))

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
                    yield Button("Import from Environment", variant="default", id="import-env-btn")

            yield Static("", id="keyset-edit-error")

            with Horizontal(id="keyset-save-buttons"):
                yield Button("Save & Back", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
        yield Footer()

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
        return manager.store.key_sets.get(self._keyset_name or "")  # type: ignore[no-any-return]

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
        try:
            env_input = self.query_one("#env-var-input", Input)
        except Exception:
            return
        if provider == "__custom__":
            env_input.value = ""
            env_input.placeholder = "Enter any environment variable name..."
            env_input.focus()
        elif provider:
            env_var = PROVIDER_KEY_MAP.get(provider, "")
            if env_var:
                env_input.value = env_var
                env_input.placeholder = "OPENAI_API_KEY"

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

    def action_add_key(self) -> None:
        """Add key via keyboard shortcut."""
        self.handle_add_key()

    def action_import_env(self) -> None:
        """Import from environment via keyboard shortcut."""
        self.handle_import_env()

    def action_edit_selected_key(self) -> None:
        """Edit the currently selected key's value."""
        table = self.query_one("#keys-table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if row_key is None or row_key.row_key is None:
                return  # type: ignore[unreachable]
            env_var = str(row_key.row_key.value)
        except Exception:
            return

        ks = self._get_keyset()
        if ks is None:
            return
        entry = ks.keys.get(env_var)
        if entry is None:
            return

        def on_dismiss(new_value: str | None) -> None:
            if new_value is None:
                return  # cancelled
            try:
                update_key_value(ks, env_var, new_value or None)
            except KeyError:
                return
            manager = getattr(self.app, "store_manager", None)
            if manager:
                manager.save()
            self._refresh_table()

        self.app.push_screen(
            EditKeyValueModal(entry.provider, env_var, entry.value),
            on_dismiss,
        )

    def action_delete_selected_key(self) -> None:
        """Delete the currently selected key."""
        table = self.query_one("#keys-table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
            if row_key is None or row_key.row_key is None:
                return  # type: ignore[unreachable]
            env_var = str(row_key.row_key.value)
        except Exception:
            return

        ks = self._get_keyset()
        if ks is None:
            return
        if env_var not in ks.keys:
            return

        def on_dismiss(confirmed: object) -> None:
            if not isinstance(confirmed, bool) or not confirmed:
                return
            try:
                remove_key(ks, env_var)
            except KeyError:
                return
            manager = getattr(self.app, "store_manager", None)
            if manager:
                manager.save()
            self._refresh_table()

        self.app.push_screen(
            ConfirmDeleteScreen(message=f"Remove '{env_var}' from this key set?"),
            on_dismiss,
        )

    @on(Button.Pressed, "#import-env-btn")
    def handle_import_env(self) -> None:
        """Import keys from environment with merge preview."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return

        # Ensure key set exists
        if self._is_new:
            try:
                name_input = self.query_one("#name-input", Input)
                name = name_input.value.strip()
            except Exception:
                return
            if not name:
                self._show_error("Enter a key set name first, then import")
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

        preview = compute_merge(ks)

        # Check if nothing to import
        if (
            not preview.new
            and not preview.overlap
            and not preview.orphan_stored
            and not preview.orphan_env_fallback
        ):
            self._show_error("No known API keys found in environment")
            return

        def on_dismiss(result: object) -> None:
            if result is None:
                return  # cancelled
            manager.save()
            self._refresh_table()

        self.app.push_screen(
            MergeImportModal(preview, ks),
            on_dismiss,
        )

    def _show_error(self, message: str) -> None:
        try:
            error_widget = self.query_one("#keyset-edit-error", Static)
            error_widget.update(message)
        except Exception:
            pass
