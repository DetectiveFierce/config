# Niri Keymap

Caps Lock is Hyper and is exposed to niri as `Mod`. `Mod` controls windows and
workspaces; `Super` launches applications and commands.

| Keys | Action |
| --- | --- |
| `Mod+H/L` | Focus column left/right |
| `Mod+J/K` | Focus workspace down/up |
| `Mod+Ctrl+H/L` | Move column left/right |
| `Mod+Ctrl+J/K` | Move column to workspace down/up |
| `Mod+Shift+H/J/K/L` | Focus adjacent monitor |
| `Mod+Ctrl+Shift+H/J/K/L` | Move column to adjacent monitor |
| `Mod+1…9` | Focus workspace by index |
| `Mod+Ctrl+1…9` | Move column to workspace by index |
| `Mod+R` | Cycle column width |
| `Mod+F` / `Mod+Shift+F` | Maximize column / fullscreen window |
| `Mod+V` | Toggle floating |
| `Mod+W` | Toggle tabbed column |
| `Super+Q` | Close focused window |
| `Super+T` | Open Ghostty |
| `Super+Return` | Open Kitty |
| `Super+D` | Open application launcher |
| `Super+L` | Lock session |
| `Super+P` | Open niri's native frozen screenshot UI |
| `Super+Shift+P` | Pick and copy a color |
| `Super+Ctrl+C/F/R/T` | Launch app in focused window directory |

Run `Mod+Shift+Slash` for niri's live hotkey overlay. The complete definitions
are split by concern under `binds/`.
