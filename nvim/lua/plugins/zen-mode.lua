return {
  "shortcuts/no-neck-pain.nvim",
  event = "BufReadPre",
  opts = {
    width = 80,
    buffers = {
      right = { enabled = true },
      left = { enabled = false },
    },
    options = {
      wrap = true,              -- enable line wrap
      linebreak = true,         -- wrap at word boundaries
      breakindent = true,       -- indent wrapped lines
      breakindentopt = "shift:2", -- 2 spaces of visual indent
      showbreak = "  ",         -- visual prefix for wrapped lines
    },
  },
  config = function(_, opts)
    require("no-neck-pain").setup(opts)

    -- Match side column background
    vim.api.nvim_set_hl(0, "NoNeckPainWidthUp",   { bg = "#22350a" })
    vim.api.nvim_set_hl(0, "NoNeckPainWidthDown", { bg = "#22350a" })
  end,
}
