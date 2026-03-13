#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.json"
SKILLS_SRC = Path(__file__).parent / "skills"
PROMPTS_SRC = Path(__file__).parent / "prompts"


def edit_config(config: dict) -> dict:
    overlay_path = Path(__file__).parent / "config" / "opencode.json"

    assert overlay_path.exists(), "Config overlay not present"
    with open(overlay_path) as f:
        overlay = json.load(f)

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


def install_stow():
    print("\nInstalling files...")
    dest = Path.home() / ".config" / "opencode"
    skills_dest = dest / "skills"
    prompts_dest = dest / "prompts"

    skills_dest.mkdir(parents=True, exist_ok=True)
    prompts_dest.mkdir(parents=True, exist_ok=True)

    if SKILLS_SRC.exists():
        subprocess.run(
            [
                "stow",
                "-t",
                str(skills_dest),
                "-d",
                str(SKILLS_SRC.parent),
                SKILLS_SRC.name,
            ],
            check=True,
        )
        print(f"  Installed skills to: {skills_dest}")
    else:
        print(f"  No skills source found at: {SKILLS_SRC}, skipping")

    if PROMPTS_SRC.exists():
        subprocess.run(
            [
                "stow",
                "-t",
                str(prompts_dest),
                "-d",
                str(PROMPTS_SRC.parent),
                PROMPTS_SRC.name,
            ],
            check=True,
        )
        print(f"  Installed prompts to: {prompts_dest}")
    else:
        print(f"  No prompts source found at: {PROMPTS_SRC}, skipping")

    print("\nInstallation complete!")


def main():
    ensure_config()
    install_stow()


if __name__ == "__main__":
    main()
