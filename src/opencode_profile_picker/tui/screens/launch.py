"""Launch screen — resolve keys, show summary, and launch OpenCode."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from opencode_profile_picker.config.paths import get_omo_config_paths
from opencode_profile_picker.keys.launcher import check_opencode_available, launch_opencode
from opencode_profile_picker.keys.resolver import (
    build_launch_env,
    get_required_keys,
    resolve_keys,
)
from opencode_profile_picker.presets.applier import apply_preset


class LaunchScreen(Screen[None]):
    """Screen showing launch summary and executing the launch."""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("ctrl+l", "launch", "Launch"),
    ]

    CSS = """
    #launch-container {
        width: 100%;
        max-width: 60;
        height: auto;
        align: center middle;
        border: solid $primary;
        padding: 1 2;
    }

    #launch-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }

    #launch-summary {
        padding: 1 0;
    }

    #launch-error {
        color: $error;
        padding-top: 1;
    }

    #launch-buttons {
        padding-top: 1;
        align: center middle;
    }
    """

    def __init__(self, profile_name: str) -> None:
        super().__init__()
        self._profile_name = profile_name

    def compose(self) -> ComposeResult:
        with Container(id="launch-container"):
            yield Label(f"Launch: {self._profile_name}", id="launch-title")
            yield Static("", id="launch-summary")
            yield Static("", id="launch-error")
            with Horizontal(id="launch-buttons"):
                yield Button("Launch", variant="primary", id="launch-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
        yield Footer()

    def on_mount(self) -> None:
        self._build_summary()

    def _build_summary(self) -> None:
        """Build the launch summary."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        discovery = getattr(app, "discovery", None)

        if manager is None:
            return

        profile = manager.store.profiles.get(self._profile_name)
        if profile is None:
            return

        keyset = manager.store.key_sets.get(profile.key_set)
        required = set()
        if discovery:
            required = get_required_keys(profile.preset, discovery)

        lines = [
            f"Profile: {profile.name}",
            f"Preset: {profile.preset}",
            f"Key Set: {profile.key_set}",
            "",
            "Keys to inject:",
        ]

        if keyset:
            resolved = resolve_keys(keyset, required)
            for key, value in sorted(resolved.items()):
                if key.startswith("UNKNOWN:"):
                    lines.append(f"  ? {key} (unknown provider)")
                elif value:
                    lines.append(f"  ✓ {key} (resolved)")
                else:
                    lines.append(f"  ✗ {key} (missing)")
        else:
            lines.append("  Key set not found!")

        summary = self.query_one("#launch-summary", Static)
        summary.update("\n".join(lines))

    @on(Button.Pressed, "#launch-btn")
    def handle_launch(self) -> None:
        """Execute the launch."""
        app = self.app
        manager = getattr(app, "store_manager", None)
        discovery = getattr(app, "discovery", None)

        if manager is None:
            return

        profile = manager.store.profiles.get(self._profile_name)
        if profile is None:
            self._show_error("Profile not found")
            return

        keyset = manager.store.key_sets.get(profile.key_set)
        if keyset is None:
            self._show_error("Key set not found")
            return

        required = set()
        if discovery:
            required = get_required_keys(profile.preset, discovery)

        # Resolve keys
        resolved = resolve_keys(keyset, required)

        # Check opencode
        if not check_opencode_available():
            self._show_error("OpenCode not found on PATH")
            return

        # Apply preset
        config_paths = get_omo_config_paths()
        for path in config_paths:
            if path.exists():
                preset_result = apply_preset(path, profile.preset)
                if not preset_result.success:
                    # Warn but continue
                    pass
                break

        # Build env and launch
        env = build_launch_env(resolved)
        launch_result = launch_opencode(env)

        if launch_result.success:
            self.app.exit()
        else:
            self._show_error(launch_result.message)

    @on(Button.Pressed, "#cancel-btn")
    def handle_cancel(self) -> None:
        self.dismiss()

    def action_launch(self) -> None:
        """Launch via keyboard shortcut."""
        self.handle_launch()

    def _show_error(self, message: str) -> None:
        try:
            error_widget = self.query_one("#launch-error", Static)
            error_widget.update(message)
        except Exception:
            pass
