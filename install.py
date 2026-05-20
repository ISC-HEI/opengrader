#!/usr/bin/env python3
# Installs OpenGrader into the opencode config directory (~/.config/opencode).
#
# Two things happen:
#   1. The opencode.json agent config is deep-merged into the user's existing
#      opencode config, so we don't clobber any other agents or settings they have.
#   2. skills/ and prompts/ are symlinked (via stow) into ~/.config/opencode/,
#      so edits in this repo are immediately live without reinstalling.
#
# Reinstall is only needed when adding new skill directories, renaming files,
# or changing config/opencode.json. Day-to-day edits to existing files are
# picked up automatically through the symlinks.

import json
import shutil
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"
SKILLS_SRC = Path(__file__).parent / "skills"
PROMPTS_SRC = Path(__file__).parent / "prompts"


def edit_config(config: dict) -> dict:
    overlay_path = Path(__file__).parent / "config" / "opencode.json"

    assert overlay_path.exists(), "Config overlay not present"
    with open(overlay_path) as f:
        overlay = json.load(f)

    # Deep merge so nested dicts (e.g. other agents' permission blocks) are
    # preserved rather than replaced wholesale by our overlay.
    def deep_merge(base: dict, overlay: dict) -> dict:
        result = base.copy()
        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    config = deep_merge(config, overlay)

    return config


def ensure_config():
    print("Setting up config...")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Created config directory: {CONFIG_PATH.parent}")

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        print(f"  Loaded existing config: {CONFIG_PATH}")
    else:
        config = {}
        print("  No existing config found, starting fresh")

    config = edit_config(config)

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Saved config to: {CONFIG_PATH}")


def clear_stale_entries(src: Path, dest: Path):
    # Only remove entries that belong to us (same name as something in src).
    # This leaves any other skills or prompts the user has installed untouched.
    for entry in src.iterdir():
        target = dest / entry.name
        if target.exists() or target.is_symlink():
            target.unlink() if target.is_symlink() else shutil.rmtree(target)
            print(f"  Removed stale entry: {target}")


def install_stow():
    print("\nInstalling files...")
    dest = Path.home() / ".config" / "opencode"
    skills_dest = dest / "skills"
    prompts_dest = dest / "prompts"

    skills_dest.mkdir(parents=True, exist_ok=True)
    prompts_dest.mkdir(parents=True, exist_ok=True)

    if SKILLS_SRC.exists():
        clear_stale_entries(SKILLS_SRC, skills_dest)
        for entry in SKILLS_SRC.iterdir():
            (skills_dest / entry.name).symlink_to(entry.resolve())
        print(f"  Installed skills to: {skills_dest}")
    else:
        print(f"  No skills source found at: {SKILLS_SRC}, skipping")

    if PROMPTS_SRC.exists():
        clear_stale_entries(PROMPTS_SRC, prompts_dest)
        for entry in PROMPTS_SRC.iterdir():
            (prompts_dest / entry.name).symlink_to(entry.resolve())
        print(f"  Installed prompts to: {prompts_dest}")
    else:
        print(f"  No prompts source found at: {PROMPTS_SRC}, skipping")

    print("\nInstallation complete!")


def main():
    ensure_config()
    install_stow()


if __name__ == "__main__":
    main()
