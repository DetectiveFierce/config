return {
  "mg979/vim-visual-multi",
  branch = "master",
  init = function()
    -- Fully disable all default mappings to avoid conflicts/warnings
    vim.g.VM_default_mappings = 0
    vim.g.VM_maps = {
      ["Find Under"]          = "<C-n>",
      ["Find Subword Under"]  = "<C-n>",
      ["Select All"]          = "<C-S-n>",
      ["Skip Region"]         = "q",        -- safe placeholder

      -- Move cursor up/down with Ctrl+Alt+Arrow (GUI/terminal dependent)
      ["Add Cursor Up"]       = "<C-M-Up>",
      ["Add Cursor Down"]     = "<C-M-Down>",
    }
  end,
}
