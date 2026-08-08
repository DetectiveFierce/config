return {
  "neovim/nvim-lspconfig",
  config = function()
    local lspconfig = require("lspconfig")

    -- LaTeX LSP
    lspconfig.texlab.setup({})

    -- Lua LSP for Neovim config and plugins
    lspconfig.lua_ls.setup({
      settings = {
        Lua = {
          diagnostics = {
            enable = true,
            globals = { "vim" },
          },
          workspace = {
            checkThirdParty = false,
            library = vim.api.nvim_get_runtime_file("", true),
          },
        },
      },
    })

    -- Keymaps when LSP attaches
    vim.api.nvim_create_autocmd("LspAttach", {
      group = vim.api.nvim_create_augroup("UserLspConfig", {}),
      callback = function(ev)
        vim.bo[ev.buf].omnifunc = "v:lua.vim.lsp.omnifunc"
        local opts = { buffer = ev.buf }
        vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
        vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
        vim.keymap.set("n", "gR", vim.lsp.buf.rename, opts)
        vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
      end,
    })

    -- Trigger diagnostics on save
    vim.api.nvim_create_autocmd("BufWritePost", {
      pattern = "*.lua",
      callback = function()
        vim.diagnostic.setqflist({ open = false })
      end,
    })

    -- Optional: diagnostic display config
    vim.diagnostic.config({
      virtual_text = true,
      signs = true,
      update_in_insert = false,
      severity_sort = true,
    })
  end,
}
