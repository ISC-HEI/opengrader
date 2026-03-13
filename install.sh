#!/bin/bash

DEST="$HOME/.config/opencode"

SKILL_DEST="$DEST/skills"
PROMPT_DEST="$DEST/prompts"

mkdir -p "$DEST/skills" "$DEST/prompts"

stow -t "$SKILL_DEST" skills && echo "Installed skills"

stow -t "$PROMPT_DEST" prompts && echo "Intalled prompts"
