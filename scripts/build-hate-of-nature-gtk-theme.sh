#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATPPUCCIN_THEME_NAME="catppuccin-mocha-green-standard+default"
CATPPUCCIN_RELEASE_URL="https://github.com/catppuccin/gtk/releases/download/v1.0.3/${CATPPUCCIN_THEME_NAME}.zip"
SRC_THEME_ARG="${1:-}"
DST_THEME="${2:-$ROOT_DIR/Hate of Nature GTK Theme}"
TEMP_SOURCE_DIR=""

cleanup() {
  if [[ -n "$TEMP_SOURCE_DIR" && -d "$TEMP_SOURCE_DIR" ]]; then
    rm -rf "$TEMP_SOURCE_DIR"
  fi
}

trap cleanup EXIT

download_catppuccin_source() {
  TEMP_SOURCE_DIR="$(mktemp -d)"
  local archive="$TEMP_SOURCE_DIR/${CATPPUCCIN_THEME_NAME}.zip"
  local extracted="$TEMP_SOURCE_DIR/$CATPPUCCIN_THEME_NAME"

  echo "Source theme not found locally. Downloading Catppuccin Mocha base..." >&2
  curl --fail --silent --show-error --location \
    -o "$archive" \
    "$CATPPUCCIN_RELEASE_URL"
  unzip -q "$archive" -d "$TEMP_SOURCE_DIR"

  if [[ ! -d "$extracted" ]]; then
    echo "error: downloaded archive did not contain $CATPPUCCIN_THEME_NAME" >&2
    exit 1
  fi

  printf '%s\n' "$extracted"
}

resolve_source_theme() {
  local requested="${1:-}"
  if [[ -n "$requested" ]]; then
    if [[ ! -d "$requested" ]]; then
      echo "error: source theme not found: $requested" >&2
      exit 1
    fi
    printf '%s\n' "$requested"
    return
  fi

  local -a candidates=(
    "$ROOT_DIR/catppuccin-mocha-green-standard+default"
    "$HOME/.local/share/themes/catppuccin-mocha-green-standard+default"
    "$HOME/.local/share/themes/catppuccin-mocha-green-standard+default-dark"
    "$HOME/.themes/catppuccin-mocha-green-standard+default"
    "$HOME/.themes/catppuccin-mocha-green-standard+default-dark"
    "/usr/share/themes/catppuccin-mocha-green-standard+default"
    "/usr/share/themes/catppuccin-mocha-green-standard+default-dark"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -d "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
  done

  download_catppuccin_source
}

SRC_THEME="$(resolve_source_theme "$SRC_THEME_ARG")"

rm -rf "$DST_THEME"
mkdir -p "$DST_THEME"
cp -a "$SRC_THEME"/. "$DST_THEME"/

if [[ -f "$DST_THEME/index.theme" ]]; then
  perl -0pi -e '
    s/^Name\s*=\s*.*$/Name=Hate-of-Nature/m;
    s/^Comment\s*=\s*.*$/Comment=Hate of Nature green Catppuccin-Mocha GTK theme/m;
    s/^GtkTheme\s*=\s*.*$/GtkTheme=Hate-of-Nature/m;
    s/^MetacityTheme\s*=\s*.*$/MetacityTheme=Hate-of-Nature/m;
  ' "$DST_THEME/index.theme"
fi

mapfile -d '' text_files < <(
  find "$DST_THEME" -type f -regextype posix-extended -regex '.*(\.(css|scss|svg|rc|xml|theme|ini|md)|/gtkrc)$' -print0
)

for file in "${text_files[@]}"; do
  perl -0pi -e '
    # Catppuccin Mocha foundational roles -> Hate-of-Nature dark roles.
    s/#11111b\b/#0D1303/gi; # crust
    s/#181825\b/#131F00/gi; # mantle
    s/#1e1e2e\b/#172304/gi; # base
    s/#313244\b/#223401/gi; # surface0
    s/#45475a\b/#2E4012/gi; # surface1
    s/#585b70\b/#3A5412/gi; # surface2
    s/#6c7086\b/#485731/gi; # overlay0
    s/#7f849c\b/#57702F/gi; # overlay1
    s/#9399b2\b/#61704A/gi; # overlay2
    s/#a6adc8\b/#61704A/gi; # subtext0
    s/#bac2de\b/#92B161/gi; # subtext1
    s/#cdd6f4\b/#E4F0D4/gi; # text
    s/#eff1f5\b/#E4F0D4/gi; # common compiled text token
    s/#ffffff\b/#F8F8F2/gi; # preserve high-contrast foregrounds

    # Catppuccin accent slots -> monochrome green family.
    s/#f5e0dc\b/#92B161/gi; # rosewater
    s/#f2cdcd\b/#86B42B/gi; # flamingo
    s/#f5c2e7\b/#92B161/gi; # pink
    s/#cba6f7\b/#5A8A22/gi; # mauve
    s/#f38ba8\b/#5A8A22/gi; # red
    s/#eba0ac\b/#4A6B1A/gi; # maroon
    s/#fab387\b/#A6E22E/gi; # peach
    s/#f9e2af\b/#92B161/gi; # yellow
    s/#a6e3a1\b/#A6E22E/gi; # green
    s/#94e2d5\b/#92B161/gi; # teal
    s/#89dceb\b/#92B161/gi; # sky
    s/#74c7ec\b/#86B42B/gi; # sapphire
    s/#89b4fa\b/#86B42B/gi; # blue
    s/#b4befe\b/#92B161/gi; # lavender

    # Common compiled derivatives from Catppuccin build output.
    s/#14141f\b/#131F00/gi;
    s/#0b0b12\b/#0D1303/gi;
    s/#0a0a0f\b/#0D1303/gi;
    s/#060609\b/#000000/gi;
    s/#393947\b/#2E4012/gi;
    s/#484856\b/#3A5412/gi;
    s/#333342\b/#223401/gi;
    s/#282938\b/#223401/gi;
    s/#5d5d6a\b/#485731/gi;
    s/#4d4d54\b/#485731/gi;
    s/#444556\b/#485731/gi;
    s/#3d3e4c\b/#3A5412/gi;
    s/#35353d\b/#2E4012/gi;
    s/#34343f\b/#2E4012/gi;
    s/#32333c\b/#2E4012/gi;
    s/#292936\b/#223401/gi;
    s/#242434\b/#223401/gi;
    s/#222234\b/#172304/gi;
  ' "$file"
done

# Enforce readable text tokens and deep backgrounds for GTK3/GTK4.
for css in "$DST_THEME"/gtk-3.0/gtk*.css "$DST_THEME"/gtk-4.0/gtk*.css; do
  [[ -f "$css" ]] || continue
  perl -0pi -e '
    s/@define-color theme_fg_color .*?;/@define-color theme_fg_color #E4F0D4;/g;
    s/@define-color theme_text_color .*?;/@define-color theme_text_color #E4F0D4;/g;
    s/@define-color fg_color .*?;/@define-color fg_color #E4F0D4;/g;
    s/@define-color text_color .*?;/@define-color text_color #E4F0D4;/g;

    s/(\bbackground[^;\n]*?)#F8F8F2\b/$1#131F00/gi;
    s/(\bbackground[^;\n]*?)#E4F0D4\b/$1#131F00/gi;
    s/(\bbackground[^;\n]*?)#fff\b/$1#131F00/gi;
    s/(\bbackground[^;\n]*?)#ffffff\b/$1#131F00/gi;
    s/(\bbackground[^;\n]*?)\bwhite\b/$1#131F00/gi;
    s/(\bbackground[^;\n]*?)rgba\(\s*248\s*,\s*248\s*,\s*242\s*,\s*([0-9.]+)\s*\)/$1rgba(19, 31, 0, $2)/gi;
    s/(\bbackground[^;\n]*?)rgba\(\s*228\s*,\s*240\s*,\s*212\s*,\s*([0-9.]+)\s*\)/$1rgba(19, 31, 0, $2)/gi;
    s/(\bbackground[^;\n]*?)rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\s*\)/$1rgba(19, 31, 0, $2)/gi;
  ' "$css"
done

# Centralized deep-dark overrides for app-specific and widget-specific polish.
for css in "$DST_THEME"/gtk-3.0/gtk*.css "$DST_THEME"/gtk-4.0/gtk*.css; do
  [[ -f "$css" ]] || continue
  {
    echo
    echo "/* Hate-of-Nature centralized overrides */"
    cat "$ROOT_DIR/scripts/hate-of-nature-gtk-overrides.css"
  } >> "$css"
done

# GTK2 color scheme values use inline key:value pairs.
if [[ -f "$DST_THEME/gtk-2.0/gtkrc" ]]; then
  perl -0pi -e '
    s/text_color:[^\\n"]+/text_color:#E4F0D4/g;
    s/base_color:[^\\n"]+/base_color:#131F00/g;
    s/fg_color:[^\\n"]+/fg_color:#E4F0D4/g;
    s/bg_color:[^\\n"]+/bg_color:#162400/g;
    s/selected_fg_color:[^\\n"]+/selected_fg_color:#E4F0D4/g;
    s/selected_bg_color:[^\\n"]+/selected_bg_color:#92B161/g;
    s/wm_color:[^\\n"]+/wm_color:#E4F0D4/g;
    s/unfocused_wm_color:[^\\n"]+/unfocused_wm_color:#61704A/g;
    s/panel_bg_color:[^\\n"]+/panel_bg_color:#131F00/g;
    s/panel_fg_color:[^\\n"]+/panel_fg_color:#E4F0D4/g;
    s/dark_text_color:[^\\n"]+/dark_text_color:#E4F0D4/g;
    s/dark_base_color:[^\\n"]+/dark_base_color:#131F00/g;
    s/dark_fg_color:[^\\n"]+/dark_fg_color:#E4F0D4/g;
    s/dark_bg_color:[^\\n"]+/dark_bg_color:#162400/g;
    s/sidebar_bg:[^\\n"]+/sidebar_bg:#172304/g;
    s/sidebar_fg:[^\\n"]+/sidebar_fg:#92B161/g;
  ' "$DST_THEME/gtk-2.0/gtkrc"
fi

# Final pass: clamp any remaining colors to the approved palette.
"$ROOT_DIR/scripts/normalize-hate-of-nature-gtk-theme-colors.pl" --include-assets "$DST_THEME"

# Deep-dark surface pass: after normalization, force bright background tokens
# in GTK3/GTK4 CSS back to dark surfaces.
for css in "$DST_THEME"/gtk-3.0/gtk*.css "$DST_THEME"/gtk-4.0/gtk*.css; do
  [[ -f "$css" ]] || continue
  perl -0pi -e '
    my @lines = split /\n/, $_, -1;
    for my $line (@lines) {
      if ($line =~ /^\s*background(?:-color|-image)?\s*:/i) {
        $line =~ s/#F8F8F2\b/#131F00/gi;
        $line =~ s/#E4F0D4\b/#131F00/gi;
        $line =~ s/#fff\b/#131F00/gi;
        $line =~ s/#ffffff\b/#131F00/gi;
        $line =~ s/\bwhite\b/#131F00/gi;
        $line =~ s/\bwhitesmoke\b/#131F00/gi;
        $line =~ s/rgba\(\s*248\s*,\s*248\s*,\s*242\s*,\s*([0-9.]+)\s*\)/rgba(19, 31, 0, $1)/gi;
        $line =~ s/rgba\(\s*228\s*,\s*240\s*,\s*212\s*,\s*([0-9.]+)\s*\)/rgba(19, 31, 0, $1)/gi;
        $line =~ s/rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\s*\)/rgba(19, 31, 0, $1)/gi;
      }

      # Tint white text toward soft green without touching backgrounds.
      if ($line =~ /^\s*color\s*:/i) {
        $line =~ s/#F8F8F2\b/#E4F0D4/gi;
        $line =~ s/rgba\(\s*248\s*,\s*248\s*,\s*242\s*,\s*([0-9.]+)\s*\)/rgba(228, 240, 212, $1)/gi;
      }

      if ($line =~ /^\s*caret-color\s*:/i) {
        $line =~ s/#F8F8F2\b/#E4F0D4/gi;
        $line =~ s/rgba\(\s*248\s*,\s*248\s*,\s*242\s*,\s*([0-9.]+)\s*\)/rgba(228, 240, 212, $1)/gi;
      }
    }
    $_ = join("\n", @lines);
  ' "$css"
done

# Final sanitation: GTK CSS rejects `!important`, so scrub it after every
# transformation stage in case upstream content or later normalization
# reintroduced it.
for css in "$DST_THEME"/gtk-3.0/gtk*.css "$DST_THEME"/gtk-4.0/gtk*.css; do
  [[ -f "$css" ]] || continue
  perl -0pi -e 's/\s+!important\b//g' "$css"
done

if [[ -f "$DST_THEME/index.theme" ]]; then
  sed -i 's/^Name=.*/Name=Hate-of-Nature/' "$DST_THEME/index.theme"
fi

echo "Built theme in: $DST_THEME"
