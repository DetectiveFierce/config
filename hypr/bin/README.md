# hypr-alttab binary

This directory vendors a prebuilt `hypr-alttab` binary so Caps+Tab switching
works on machines where the tool is not installed system-wide.

Current binary source:
`https://github.com/kanak-buet19/hypr-dock` (commit `2865e7e`)

To refresh the binary:

```bash
cd ~/.cache/hypr-dock-codex
make build
cp -p bin/hypr-alttab ~/config/hypr/bin/hypr-alttab
```

The runtime configuration for this binary is in:

`~/config/hypr-dock/switcher.jsonc`
