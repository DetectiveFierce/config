return {
    "L3MON4D3/LuaSnip",
    version = "v2.*",
    build = "make install_jsregexp",
    config = function()
        require("luasnip").config.set_config({
            enable_autosnippets = true,
        })

        require("luasnip.loaders.from_lua").lazy_load({
            paths = "~/.config/nvim/snippets",
        })
    end,
}
