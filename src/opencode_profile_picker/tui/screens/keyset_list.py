"""Key set list screen."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Label, Static

from opencode_profile_picker.profiles.operations import (
    delete_key_set,
    list_key_sets,
)
from opencode_profile_picker.tui.screens.confirm_delete import ConfirmDeleteScreen
from opencode_profile_picker.tui.screens.keyset_edit import KeySetEditScreen


class KeySetListScreen(Screen[None]):
    """Screen for browsing and managing key sets."""

    BINDINGS = [
        ("n", "new_keyset", "New"),
        ("e", "edit_keyset", "Edit"),
        ("d", "delete_keyset", "Delete"),
        ("enter", "edit_keyset", "Edit"),
        ("escape", "back", "Back"),
    ]

    CSS = """
    #keyset-list-container {
        width: 100%;
        max-width: 60;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
    }

    #keyset-list-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #keyset-list-buttons {
        padding-top: 1;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="keyset-list-container"):
            yield Label("Key Sets", id="keyset-list-title")
            yield DataTable(id="keyset-table")
            yield Static("No key sets yet.", id="keyset-empty", classes="empty-message")
            with Horizontal(id="keyset-list-buttons"):
                yield Button("New", variant="primary", id="new-btn")
                yield Button("Edit", variant="default", id="edit-btn")
                yield Button("Delete", variant="error", id="delete-btn")
                yield Button("Back", variant="default", id="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#keyset-table", DataTable)
        table.add_columns("Name", "Keys")
        table.cursor_type = "row"
        self._refresh()

    def _refresh(self) -> None:
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return

        table = self.query_one("#keyset-table", DataTable)
        table.clear()
        key_sets = list_key_sets(manager.store)

        if key_sets:
            self.query_one("#keyset-empty").add_class("hidden")
            for name, count in key_sets:
                table.add_row(name, str(count), key=name)
        else:
            self.query_one("#keyset-empty").remove_class("hidden")

    def action_new_keyset(self) -> None:
        self.app.push_screen("keyset_edit", self._on_edit_done)

    def action_edit_keyset(self) -> None:
        table = self.query_one("#keyset-table", DataTable)
        if table.row_count == 0:
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        name = str(cell_key.row_key.value)
        self.app.push_screen(KeySetEditScreen(name), self._on_edit_done)

    def action_delete_keyset(self) -> None:
        table = self.query_one("#keyset-table", DataTable)
        if table.row_count == 0:
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        name = str(cell_key.row_key.value)
        self.app.push_screen(
            ConfirmDeleteScreen(message=f"Delete key set '{name}'?"),
            self._on_delete_result,
        )

    def action_back(self) -> None:
        self.dismiss()

    @on(Button.Pressed, "#new-btn")
    def handle_new(self) -> None:
        self.action_new_keyset()

    @on(Button.Pressed, "#edit-btn")
    def handle_edit(self) -> None:
        self.action_edit_keyset()

    @on(Button.Pressed, "#delete-btn")
    def handle_delete(self) -> None:
        self.action_delete_keyset()

    @on(Button.Pressed, "#back-btn")
    def handle_back(self) -> None:
        self.dismiss()

    def _on_edit_done(self, _result: object) -> None:
        self._refresh()

    def _on_delete_result(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        app = self.app
        manager = getattr(app, "store_manager", None)
        if not manager:
            return
        table = self.query_one("#keyset-table", DataTable)
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        name = str(cell_key.row_key.value)
        try:
            delete_key_set(manager.store, name)
            manager.save()
        except KeyError:
            pass
        self._refresh()
