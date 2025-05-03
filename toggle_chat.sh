#!/bin/bash

APP_CLASS="KagiChatPopup"
#CHANGE ME!
PYTHON_SCRIPT_PATH="/home/gingi/.config/hypr/fastgpt/main.py"

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it (e.g., sudo pacman -S jq)" >&2
    exit 1
fi

WINDOW_INFO=$(hyprctl clients -j | jq -e --arg CLASS "$APP_CLASS" '.[] | select(.class == $CLASS)')

if [ -z "$WINDOW_INFO" ]; then
  nohup python "$PYTHON_SCRIPT_PATH" > /dev/null 2>&1 &
else
  ADDRESS=$(echo "$WINDOW_INFO" | jq -r '.address')
  WORKSPACE_ID=$(echo "$WINDOW_INFO" | jq -r '.workspace.id')
  ACTIVE_WORKSPACE_ID=$(hyprctl activeworkspace -j | jq -r '.id')

  if [ "$WORKSPACE_ID" != "$ACTIVE_WORKSPACE_ID" ]; then
      hyprctl dispatch movetoworkspace "$ACTIVE_WORKSPACE_ID,address:$ADDRESS"
  fi
  hyprctl dispatch focuswindow address:$ADDRESS
fi

exit 0 