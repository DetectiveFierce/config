return {
    "hrsh7th/nvim-cmp",
    dependencies = { "hrsh7th/cmp-nvim-lsp" },
    config = function()
        local cmp = require("cmp")
        cmp.setup({
            sources = cmp.config.sources({
                { name = "nvim_lsp" },
                { name = "buffer" },
            }),
            mapping = cmp.mapping.preset.insert({
                ["<C-Space>"] = cmp.mapping.complete(),
                ["<C-u>"] = cmp.mapping.scroll_docs(-4),
                ["<C-d>"] = cmp.mapping.scroll_docs(4),
                ["<C-l>"] = cmp.mapping.confirm({ select = true }),
            }),
        })
    end,
}
