typeset -U path PATH
path=(
  "$HOME/bin"
  "$HOME/.local/bin"
  "$HOME/.local/share/pnpm"
  "$HOME/.bun/bin"
  "$HOME/.ghcup/bin"
  "$HOME/.cabal/bin"
  "$HOME/.local/share/gem/ruby/3.4.0/bin"
  /opt/depot_tools
  /usr/bin/sioyek
  $path
)

# Prefer system toolchain over rustup shims when both are present.
path=(${path:#$HOME/.cargo/bin})
path+=("$HOME/.cargo/bin")

export PNPM_HOME="$HOME/.local/share/pnpm"
export BUN_INSTALL="$HOME/.bun"

# Oh My Zsh is an external, pinned dependency installed by `./dotfiles bootstrap`.
export ZSH="${XDG_DATA_HOME:-$HOME/.local/share}/oh-my-zsh"
ZSH_THEME="spaceship"

# Spaceship: keep prompt concise and arrow-based
SPACESHIP_PROMPT_ADD_NEWLINE=false
SPACESHIP_CHAR_SYMBOL="➜"
SPACESHIP_CHAR_SUFFIX=" "
SPACESHIP_USER_SHOW=false
SPACESHIP_HOST_SHOW=false
SPACESHIP_DIR_TRUNC=1
SPACESHIP_DIR_TRUNC_REPO=false
SPACESHIP_DIR_PREFIX=" "
SPACESHIP_DIR_SUFFIX=" "
SPACESHIP_TIME_SHOW=false
SPACESHIP_EXIT_CODE_SHOW=false
SPACESHIP_GIT_STATUS_SHOW=false
SPACESHIP_GIT_BRANCH_SHOW=false
SPACESHIP_PROMPT_ORDER=(dir char)

# Ghostty-inspired Spaceship colors
SPACESHIP_PROMPT_DEFAULT_PREFIX="%F{#99cc58}"
SPACESHIP_PROMPT_DEFAULT_SUFFIX="%f"
SPACESHIP_USER_COLOR="#a6e22e"
SPACESHIP_HOST_COLOR="#66d9ef"
SPACESHIP_DIR_COLOR="#99cc58"
SPACESHIP_GIT_BRANCH_COLOR="#66d9ef"
SPACESHIP_GIT_STATUS_COLOR="#fd971f"
SPACESHIP_CHAR_COLOR_SUCCESS="#a6e22e"
SPACESHIP_CHAR_COLOR_FAILURE="#f92672"

plugins=(
  git
  sudo
  command-not-found
  colored-man-pages
  fzf
  history-substring-search
)

# fzf-tab must load before plugins that wrap ZLE widgets.
if command -v zoxide >/dev/null 2>&1; then
  plugins+=(zoxide)
fi

FZF_TAB_PLUGIN_FILE=""
if [[ -n "${ZSH:-}" ]] && [[ -d "$ZSH/plugins/fzf-tab" || -d "$ZSH/custom/plugins/fzf-tab" ]]; then
  plugins+=(fzf-tab)
elif [[ -r "/usr/share/zsh/plugins/fzf-tab/fzf-tab.plugin.zsh" ]]; then
  FZF_TAB_PLUGIN_FILE="/usr/share/zsh/plugins/fzf-tab/fzf-tab.plugin.zsh"
elif [[ -r "/usr/share/zsh/plugins/fzf-tab-git/fzf-tab.plugin.zsh" ]]; then
  FZF_TAB_PLUGIN_FILE="/usr/share/zsh/plugins/fzf-tab-git/fzf-tab.plugin.zsh"
elif [[ -r "/usr/share/zsh/plugins/fzf-tab-source/fzf-tab.plugin.zsh" ]]; then
  FZF_TAB_PLUGIN_FILE="/usr/share/zsh/plugins/fzf-tab-source/fzf-tab.plugin.zsh"
fi
plugins+=(zsh-autosuggestions zsh-syntax-highlighting)

if [[ -n "${ZSH:-}" ]] && [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
  source "$ZSH/oh-my-zsh.sh"
fi
if [[ -n "${FZF_TAB_PLUGIN_FILE:-}" ]]; then
  source "$FZF_TAB_PLUGIN_FILE"
fi

# Custom dir section: "~" at $HOME, otherwise "/<current-dir>"
spaceship_dir() {
  [[ $SPACESHIP_DIR_SHOW == false ]] && return

  local display
  if [[ "$PWD" == "$HOME" ]]; then
    display="~"
  elif [[ "$PWD" == "/" ]]; then
    display="/"
  else
    display="/${PWD:t}"
  fi

  if (( $+functions[spaceship::section] )); then
    spaceship::section \
      --color "$SPACESHIP_DIR_COLOR" \
      --prefix "$SPACESHIP_DIR_PREFIX" \
      --suffix "$SPACESHIP_DIR_SUFFIX" \
      "$display"
  elif (( $+functions[_prompt_section] )); then
    _prompt_section \
      "$SPACESHIP_DIR_COLOR" \
      "$SPACESHIP_DIR_PREFIX" \
      "$display" \
      "$SPACESHIP_DIR_SUFFIX"
  else
    printf "%s%s%s" "$SPACESHIP_DIR_PREFIX" "$display" "$SPACESHIP_DIR_SUFFIX"
  fi
}

# Completion + tab UX
# Prefer exact results, then relax to case-insensitive and typo-tolerant matches.
zstyle ':completion:*' completer _complete _match _approximate
zstyle ':completion:*' matcher-list \
  '' \
  'm:{a-zA-Z}={A-Za-z}' \
  'r:|[._-]=* r:|=*'
zstyle ':completion:*' max-errors 1 numeric
zstyle ':completion:*' menu no
zstyle ':completion:*' group-name ''
zstyle ':completion:*' format '%F{#4d6626}  %d%f'
zstyle ':completion:*' descriptions yes
zstyle ':completion:*' verbose yes
zstyle ':completion:*' squeeze-slashes true
zstyle ':completion:*' use-cache true
zstyle ':completion:*' cache-path "$HOME/.cache/zsh"
zstyle ':completion:*' list-colors \
  'no=38;2;153;204;88' \
  'fi=38;2;153;204;88' \
  'di=38;2;166;226;46' \
  'ln=38;2;102;217;239' \
  'pi=38;2;253;151;31' \
  'so=38;2;174;43;90' \
  'ex=38;2;166;226;46'
zstyle ':fzf-tab:*' fzf-command fzf
zstyle ':fzf-tab:*' switch-group 'ctrl-left' 'ctrl-right'
zstyle ':fzf-tab:*' continuous-trigger '/'
zstyle ':fzf-tab:*' single-group color header
zstyle ':fzf-tab:*' fzf-flags \
  --height=45% \
  --layout=reverse \
  --border=rounded \
  --info=inline-right \
  --prompt='  ' \
  --pointer='›' \
  --marker='✓' \
  --separator='─' \
  --scrollbar='│' \
  --bind='tab:down,btab:up,ctrl-space:toggle,ctrl-p:toggle-preview' \
  --preview-window=right:50%:wrap:hidden \
  --ansi
zstyle ':fzf-tab:complete:*:*' fzf-preview \
  'if [[ -d $realpath ]]; then
     if command -v eza >/dev/null 2>&1; then
       eza --icons --color=always -la --group-directories-first "$realpath"
     else
       ls -lah --color=always "$realpath"
     fi
   elif [[ -f $realpath ]]; then
     if command -v bat >/dev/null 2>&1; then
       bat --style=plain --color=always --line-range :200 "$realpath"
     else
       head -200 "$realpath"
     fi
   fi'
if (( $+widgets[fzf-tab-complete] )); then
  bindkey '^I' fzf-tab-complete
fi

# Suggestions stay subtle; End accepts the whole suggestion, while Ctrl-Right
# accepts it one word at a time.
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#4d6626'
bindkey '^[[F' autosuggest-accept
bindkey '^[[1;5C' forward-word

HISTORY_SUBSTRING_SEARCH_ENSURE_UNIQUE=1
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='fg=#22350a,bg=#99cc58,bold'
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='fg=#22350a,bg=#f92672,bold'
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# History
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history
setopt SHARE_HISTORY HIST_IGNORE_ALL_DUPS HIST_SAVE_NO_DUPS HIST_FIND_NO_DUPS
setopt INTERACTIVE_COMMENTS

# Zoxide
if command -v zoxide >/dev/null 2>&1; then
  eval "$(zoxide init zsh)"
  alias cd='z'
fi

# Aliases
if [[ -x "$HOME/python/venv/bin/python" ]]; then
  alias python="$HOME/python/venv/bin/python"
fi
if [[ -x "$HOME/python/venv/bin/pip" ]]; then
  alias pip="$HOME/python/venv/bin/pip"
fi
alias tmux="tmux -2"
alias create-tex="$HOME/Landing Zone/Latex Projects/create-tex.sh"

# Environment
[[ "$TERM_PROGRAM" == "vscode" ]] && unset ARGV0
[[ -f "$HOME/.ghcup/env" ]] && source "$HOME/.ghcup/env"
[[ -s "$HOME/.bun/_bun" ]] && source "$HOME/.bun/_bun"

# Ghostty-inspired fzf colors
export FZF_DEFAULT_OPTS='--color=fg:#99cc58,bg:#22350a,hl:#66d9ef,fg+:#e8ffb9,bg+:#2a4010,hl+:#a6e22e,info:#4d6626,prompt:#f92672,pointer:#a6e22e,marker:#ae81ff,spinner:#66d9ef,header:#fd971f'

if command -v neofetch >/dev/null 2>&1; then
  neofetch
elif command -v fastfetch >/dev/null 2>&1; then
  fastfetch
fi

# >>> juliaup initialize >>>

# !! Contents within this block are managed by juliaup !!

path=("$HOME/.juliaup/bin" $path)
export PATH
# Tab completion for juliaup and julia channel selection
[ -f "$HOME/.julia/juliaup/completions/zsh.zsh" ] && source "$HOME/.julia/juliaup/completions/zsh.zsh"

# <<< juliaup initialize <<<

# >>> Codex installer >>>
export PATH="$HOME/.local/bin:$PATH"
# <<< Codex installer <<<

# SSH agent for laptop key
if ! pgrep -u "$USER" ssh-agent >/dev/null; then
    eval "$(ssh-agent -s)" >/dev/null 2>&1
fi
ssh-add -l 2>/dev/null | grep -q laptop-key ||
  ssh-add ~/.ssh/laptop-key >/dev/null 2>&1 || true
