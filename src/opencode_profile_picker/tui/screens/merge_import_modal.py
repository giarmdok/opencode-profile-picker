"""Import merge preview modal screen."""

from __future__ import annotations

from contextlib import suppress

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Switch

from opencode_profile_picker.profiles.models import KeySet
from opencode_profile_picker.profiles.operations import MergePreview, add_key


class MergeImportModal(ModalScreen[MergePreview | None]):
    """Modal screen showing import merge preview with orphan toggles."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("i", "import", "Import"),
    ]

    CSS = """
    #merge-container {
        width: 100%;
        max-width: 55;
        height: auto;
        max-height: 90%;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }

    #merge-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #merge-scroll {
        height: auto;
        max-height: 20;
        padding-bottom: 1;
    }

    .merge-section {
        padding: 0 0 1 0;
    }

    .merge-section-title {
        text-style: bold;
        padding-bottom: 1;
    }

    .merge-row {
        padding: 0 1;
    }

    .merge-overlap {
        color: $text-muted;
    }

    #merge-buttons {
        align: center middle;
    }
    """

    def __init__(self, preview: MergePreview, key_set: KeySet) -> None:
        super().__init__()
        self._preview = preview
        self._key_set = key_set
        self._orphan_switches: dict[str, Switch] = {}
        self._orphan_env_vars: dict[str, str] = {}  # switch_id → env_var

    def compose(self) -> ComposeResult:
        with Container(id="merge-container"):
            yield Label("Import from Environment", id="merge-title")

            with VerticalScroll(id="merge-scroll"):
                # New keys section
                if self._preview.new:
                    yield Label("New keys to add:", classes="merge-section-title")
                    with Container(classes="merge-section"):
                        for entry in self._preview.new:
                            yield Label(
                                f"  {entry.provider} → {entry.env_var}",
                                classes="merge-row",
                            )

                # Overlap section (informational)
                if self._preview.overlap:
                    yield Label(
                        "Already present (no changes needed):",
                        classes="merge-section-title merge-overlap",
                    )
                    with Container(classes="merge-section merge-overlap"):
                        for entry in self._preview.overlap:
                            yield Label(
                                f"  {entry.provider} → {entry.env_var}",
                                classes="merge-row",
                            )

                # Orphan stored section (keep by default)
                if self._preview.orphan_stored:
                    yield Label(
                        "Stored keys not in environment:",
                        classes="merge-section-title",
                    )
                    with Container(classes="merge-section"):
                        for entry in self._preview.orphan_stored:
                            with Horizontal(classes="merge-row"):
                                switch_id = f"orphan-s-{entry.env_var}"
                                switch = Switch(value=True, id=switch_id)
                                self._orphan_switches[switch_id] = switch
                                self._orphan_env_vars[switch_id] = entry.env_var
                                yield Label("Keep")
                                yield switch
                                yield Label(f"   {entry.provider} → {entry.env_var}")

                # Orphan env fallback section (delete by default)
                if self._preview.orphan_env_fallback:
                    yield Label(
                        "Env-fallback keys not in environment:",
                        classes="merge-section-title",
                    )
                    with Container(classes="merge-section"):
                        for entry in self._preview.orphan_env_fallback:
                            with Horizontal(classes="merge-row"):
                                switch_id = f"orphan-f-{entry.env_var}"
                                switch = Switch(value=False, id=switch_id)
                                self._orphan_switches[switch_id] = switch
                                self._orphan_env_vars[switch_id] = entry.env_var
                                yield Label("Keep")
                                yield switch
                                yield Label(f"   {entry.provider} → {entry.env_var}")

                # Empty state
                if not any(
                    [
                        self._preview.new,
                        self._preview.overlap,
                        self._preview.orphan_stored,
                        self._preview.orphan_env_fallback,
                    ]
                ):
                    yield Label("No changes detected.", classes="merge-section")

            # Button label
            has_orphans = bool(self._preview.orphan_stored or self._preview.orphan_env_fallback)
            btn_label = "Import" if has_orphans else "Import All"

            with Horizontal(id="merge-buttons"):
                yield Button(btn_label, variant="primary", id="import-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
        yield Footer()

    @on(Button.Pressed, "#import-btn")
    def handle_import(self) -> None:
        """Apply the import: add new keys, delete toggled orphans."""
        # Add new keys
        for entry in self._preview.new:
            with suppress(ValueError):
                add_key(self._key_set, entry.provider, entry.env_var, None)

        # Delete toggled orphans
        for switch_id, switch in self._orphan_switches.items():
            if not switch.value:
                env_var = self._orphan_env_vars[switch_id]
                with suppress(KeyError):
                    del self._key_set.keys[env_var]

        self.dismiss(self._preview)

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_import(self) -> None:
        """Import via keyboard shortcut."""
        self.handle_import()
