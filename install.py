#!/usr/bin/env python3
import json
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


def symlink_dir(src: Path, dest: Path):
    """Symlink each file in src into dest, mirroring the directory structure."""
    for src_file in src.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src)
        dest_file = dest / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        if dest_file.is_symlink():
            dest_file.unlink()
        dest_file.symlink_to(src_file)


def install_files():
    print("\nInstalling files...")
    dest = Path.home() / ".config" / "opencode"

    if SKILLS_SRC.exists():
        skills_dest = dest / "skills"
        skills_dest.mkdir(parents=True, exist_ok=True)
        symlink_dir(SKILLS_SRC, skills_dest)
        print(f"  Installed skills to: {skills_dest}")
    else:
        print(f"  No skills source found at: {SKILLS_SRC}, skipping")

    if PROMPTS_SRC.exists():
        prompts_dest = dest / "prompts"
        prompts_dest.mkdir(parents=True, exist_ok=True)
        symlink_dir(PROMPTS_SRC, prompts_dest)
        print(f"  Installed prompts to: {prompts_dest}")
    else:
        print(f"  No prompts source found at: {PROMPTS_SRC}, skipping")

    print("\nInstallation complete!")


def main():
    ensure_config()
    install_files()


if __name__ == "__main__":
    main()
