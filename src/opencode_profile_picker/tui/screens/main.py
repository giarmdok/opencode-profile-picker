"""Main screen — profile list, key set summary, and actions."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Label, Static

from opencode_profile_picker.config.discover import discover_omo_config
from opencode_profile_picker.profiles.operations import (
    list_key_sets,
    list_profiles,
    validate_profiles,
)
from opencode_profile_picker.tui.screens.confirm_delete import ConfirmDeleteScreen
from opencode_profile_picker.tui.screens.launch import LaunchScreen
from opencode_profile_picker.tui.screens.profile_edit import ProfileEditScreen


class MainScreen(Screen[None]):
    """Main screen showing profiles and key sets."""

    BINDINGS = [
        ("n", "new_profile", "New"),
        ("e", "edit_profile", "Edit"),
        ("d", "delete_profile", "Delete"),
        ("k", "key_sets", "Key Sets"),
        ("l", "launch", "Launch"),
        ("enter", "edit_profile", "Edit"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="active-preset")
        with Horizontal(id="main-container"):
            with Container(id="profile-panel"):
                yield Label("Profiles", classes="section-title")
                yield DataTable(id="profile-table")
                yield Static(
                    "No profiles yet. Press N to create one.",
                    id="profile-empty",
                    classes="empty-message",
                )
            with Container(id="keyset-panel"):
                yield Label("Key Sets", classes="section-title")
                yield DataTable(id="keyset-table")
                yield Static("No key sets yet.", id="keyset-empty", classes="empty-message")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Set up tables and load data."""
        # Profile table columns
        profile_table = self.query_one("#profile-table", DataTable)
        profile_table.add_columns("Name", "Preset", "Key Set")
        profile_table.cursor_type = "row"

        # Key set table columns
        keyset_table = self.query_one("#keyset-table", DataTable)
        keyset_table.add_columns("Name", "Keys")

        # Run discovery
        app = self.app
        if hasattr(app, "store_manager"):
            app.discovery = discover_omo_config()  # type: ignore[attr-defined]

        self._refresh()

    def _refresh(self) -> None:
        """Refresh all displayed data."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        if manager is None:
            return

        store = manager.store
        discovery = getattr(app, "discovery", None)

        # Active preset
        preset_bar = self.query_one("#active-preset", Static)
        if discovery and discovery.active_preset:
            preset_bar.update(f"Active OMO preset: {discovery.active_preset}")
        elif discovery and discovery.error:
            preset_bar.update(f"OMO config: {discovery.error}")
        else:
            preset_bar.update("OMO config: not found")

        # Profiles
        profile_table = self.query_one("#profile-table", DataTable)
        profile_table.clear()
        profiles = list_profiles(store)
        orphaned = validate_profiles(store)

        if profiles:
            self.query_one("#profile-empty").add_class("hidden")
            for p in profiles:
                profile_table.add_row(
                    p.name,
                    p.preset,
                    f"{p.key_set} ⚠" if p.name in orphaned else p.key_set,
                    key=p.name,
                )
        else:
            self.query_one("#profile-empty").remove_class("hidden")

        # Key sets
        keyset_table = self.query_one("#keyset-table", DataTable)
        keyset_table.clear()
        key_sets = list_key_sets(store)

        if key_sets:
            self.query_one("#keyset-empty").add_class("hidden")
            for name, count in key_sets:
                keyset_table.add_row(name, str(count), key=name)
        else:
            self.query_one("#keyset-empty").remove_class("hidden")

        # Status bar
        status = self.query_one("#status-bar", Static)
        status.update(f"Profiles: {len(profiles)} | Key Sets: {len(key_sets)}")

    def action_new_profile(self) -> None:
        """Open the new profile screen."""
        self.app.push_screen("profile_edit", self._on_profile_edit_done)

    def action_edit_profile(self) -> None:
        """Edit the selected profile."""
        table = self.query_one("#profile-table", DataTable)
        if table.row_count == 0:
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        self.app.push_screen(
            ProfileEditScreen(str(cell_key.row_key.value)), self._on_profile_edit_done
        )

    def action_delete_profile(self) -> None:
        """Delete the selected profile."""
        table = self.query_one("#profile-table", DataTable)
        if table.row_count == 0:
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        name = str(cell_key.row_key.value)
        self.app.push_screen(
            ConfirmDeleteScreen(message=f"Delete profile '{name}'?"),
            self._on_delete_result,
        )

    def action_key_sets(self) -> None:
        """Open the key sets screen."""
        self.app.push_screen("keyset_list", self._on_keyset_done)

    def action_launch(self) -> None:
        """Launch the selected profile."""
        table = self.query_one("#profile-table", DataTable)
        if table.row_count == 0:
            return
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        self.app.push_screen(LaunchScreen(str(cell_key.row_key.value)), self._on_launch_done)

    def _on_profile_edit_done(self, _result: object) -> None:
        self._refresh()

    def _on_delete_result(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        app = self.app
        manager = getattr(app, "store_manager", None)
        if not manager:
            return
        table = self.query_one("#profile-table", DataTable)
        cell_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        profile_name = str(cell_key.row_key.value)
        from opencode_profile_picker.profiles.operations import delete_profile

        try:
            delete_profile(manager.store, profile_name)
            manager.save()
        except KeyError:
            pass
        self._refresh()

    def _on_keyset_done(self, _result: object) -> None:
        self._refresh()

    def _on_launch_done(self, _result: object) -> None:
        self._refresh()
