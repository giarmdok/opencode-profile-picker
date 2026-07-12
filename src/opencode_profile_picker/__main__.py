"""Entry point for oopps."""

from __future__ import annotations


def main() -> None:
    """Run the oopps TUI application."""
    from opencode_profile_picker.app import OoppsApp

    app = OoppsApp()
    app.run()


if __name__ == "__main__":
    main()
