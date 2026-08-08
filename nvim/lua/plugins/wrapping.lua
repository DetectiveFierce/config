return {
  "nvim-lua/plenary.nvim", -- dummy plugin
  lazy = false,
  priority = 1000,
  config = function()
    -- Core wrapping behavior
    local function enable_wrapping()
      vim.opt_local.wrap = true
      vim.opt_local.linebreak = true
      vim.opt_local.breakindent = false
      vim.opt_local.showbreak = ""
      vim.opt_local.textwidth = 0
      vim.opt_local.colorcolumn = ""
      vim.opt_local.formatoptions:append("l")
    end

    -- Apply on FileType, skip NvimTree and similar
    vim.api.nvim_create_autocmd("FileType", {
      pattern = "*",
      callback = function()
        local ft = vim.bo.filetype
        if ft ~= "NvimTree" and ft ~= "neo-tree" and ft ~= "oil" then
          enable_wrapping()
        end
      end,
    })
  end,
}
