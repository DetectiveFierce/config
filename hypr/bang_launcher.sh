#!/bin/bash

# --- Configuration ---
# Define your bang commands
declare -A BANGS
BANGS["!w"]="vivaldi https://wiki.archlinux.org/index.php?search=" # Arch Wiki
BANGS["!g"]="vivaldi https://www.google.com/search?q=" # Google Search
BANGS["!y"]="vivaldi https://www.youtube.com/results?search_query=" # YouTube
BANGS["!gh"]="google-chrome-stable https://github.com/search?q=" # GitHub
BANGS["!files"]="thunar " # Your file manager
BANGS["!term"]="kitty " # Your terminal emulator
BANGS["!edit"]="zeditor " # VS Code or your preferred editor
BANGS["!conf"]="zeditor ~/.config/" # Open Hyprland config
BANGS["!zsh"]="zeditor ~/.zshrc"
BANGS["!f"]="__FILE_SEARCH__" # Special bang to trigger file search

# File search specific settings
SEARCH_DIR="$HOME" # Base directory for file search
FILE_MANAGER="thunar" # Your preferred file manager
TERMINAL_EMULATOR="kitty" # Your preferred terminal emulator (for terminal editors)
TEXT_EDITOR="zeditor" # Your preferred GUI/CLI text editor

# Wofi/Rofi prompt
PROMPT="Run (!bangs, app, !f for files): "

# --- Functions ---

# Function to perform the file search and open the selected file
perform_file_search() {
    # Check if required tools are available
    if ! command -v fd &> /dev/null; then
        notify-send "File Search" "fd command not found. Please install fd-find."
        exit 1
    fi

    if ! command -v fzf &> /dev/null; then
        notify-send "File Search" "fzf command not found. Please install fzf."
        exit 1
    fi

    # Create a temporary file for fzf output
    local temp_file=$(mktemp)

    # Run fd and pipe to fzf in a new terminal window
    $TERMINAL_EMULATOR -e bash -c "
        echo 'Searching files... (Ctrl+E to edit, Ctrl+V to view, Enter to open)'
        fd -a -tf --color=never '' '$SEARCH_DIR' | \
        fzf --no-sort --reverse --layout=reverse --height=90% --border --inline-info \
            --expect=ctrl-e,ctrl-v \
            --preview 'bat --style=numbers --color=always {} 2>/dev/null || cat {} 2>/dev/null || echo \"Cannot preview this file\"' \
            --preview-window right:50% \
            --prompt 'Files > ' \
            --header 'Enter=open, Ctrl+E=edit, Ctrl+V=view, Esc=cancel' > '$temp_file'
    "

    # Read the result
    if [[ ! -s "$temp_file" ]]; then
        rm -f "$temp_file"
        exit 0 # User cancelled or no selection
    fi

    local result=$(cat "$temp_file")
    rm -f "$temp_file"

    local key_pressed=$(echo "$result" | head -n 1)
    local file_path=$(echo "$result" | tail -n +2 | head -n 1)

    if [[ -z "$file_path" ]]; then
        exit 0 # No file selected
    fi

    case "$key_pressed" in
        "ctrl-e") # Open with text editor
            if [[ -f "$file_path" ]]; then
                if [[ "$TEXT_EDITOR" =~ ^(nvim|helix|vim|nano)$ ]]; then
                    $TERMINAL_EMULATOR -e "$TEXT_EDITOR" "$file_path" & disown
                else
                    $TEXT_EDITOR "$file_path" & disown
                fi
            else
                notify-send "File Search" "Cannot edit directory: $file_path"
            fi
            ;;
        "ctrl-v") # Open with default application
            if [[ -d "$file_path" ]]; then
                $FILE_MANAGER "$file_path" & disown
            elif [[ -f "$file_path" ]]; then
                xdg-open "$file_path" & disown
            fi
            ;;
        *) # Default action: open appropriately
            if [[ -d "$file_path" ]]; then
                $FILE_MANAGER "$file_path" & disown
            elif [[ -f "$file_path" ]]; then
                xdg-open "$file_path" & disown
            fi
            ;;
    esac
}

# --- Main Logic ---
if command -v wofi &> /dev/null; then
    LAUNCHER_CMD="wofi --dmenu -p \"$PROMPT\" --show drun -i --allow-markup --allow-images"
elif command -v rofi &> /dev/null; then
    LAUNCHER_CMD="rofi -dmenu -p \"$PROMPT\" -show drun -i"
else
    echo "Neither wofi nor rofi found. Please install one."
    exit 1
fi

# Get user input
USER_INPUT=$(eval "$LAUNCHER_CMD")

# Exit if no input
if [[ -z "$USER_INPUT" ]]; then
    exit 0
fi

# Check for bang commands
BANG_EXECUTED=false
for bang in "${!BANGS[@]}"; do
    if [[ "$USER_INPUT" == "$bang"* ]]; then
        if [[ "${BANGS[$bang]}" == "__FILE_SEARCH__" ]]; then
            perform_file_search
            BANG_EXECUTED=true
            break
        else
            query="${USER_INPUT#$bang}"
            query="${query#"${query%%[![:space:]]*}"}" # Remove leading space
            eval "${BANGS[$bang]}\"$query\" & disown"
            BANG_EXECUTED=true
            break
        fi
    fi
done

# If no bang command was executed, try to run as application
if ! $BANG_EXECUTED; then
    # Check if it's a valid command first
    if command -v "$USER_INPUT" &> /dev/null; then
        eval "$USER_INPUT & disown"
    else
        # Try to find and execute as desktop application
        if command -v gtk-launch &> /dev/null; then
            gtk-launch "$USER_INPUT" 2>/dev/null & disown
        else
            # Fallback: try to execute directly
            eval "$USER_INPUT & disown" 2>/dev/null
        fi
    fi
fi
