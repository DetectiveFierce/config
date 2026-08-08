return {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
        require("nvim-treesitter.configs").setup({
            highlight = {
                enable = true,
                disable = { "latex", "tex" },  -- ✅ disables both variants
            },
        })
    end,
}
