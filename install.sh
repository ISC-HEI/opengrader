#!/bin/bash

declare -A OPTIONS
OPTIONS=(
    ["opencode"]="$HOME/.config/opencode/skills/"
    ["claude"]="$HOME/.claude/skills/"
    ["gemini"]="$HOME/.gemini/skills/"
)
DEST=""

if [ -n "$1" ]; then
    DEST=$1
else
  echo "No destination provided. Please choose one:"
  # Get the keys (friendly names) and add 'Custom'
  select opt in "${!OPTIONS[@]}" "Custom Path"; do
      if [ "$opt" == "Custom Path" ]; then
          read -p "Enter full path: " DEST
          break
      elif [ -n "${OPTIONS[$opt]}" ]; then
          DEST=${OPTIONS[$opt]}
          echo "Selected profile: $opt ($DEST)"
          break
      else
          echo "Invalid selection."
      fi
  done
fi

if [ -n "$DEST" ]; then
    mkdir -p $DEST
    stow -t $DEST skills && echo "Installed skills at $DEST"
else
    echo "Operation cancelled."
    exit 1
fi
