return {
    "folke/which-key.nvim",
    event = "VeryLazy",
    init = function()
        vim.o.timeout = true
        vim.o.timeoutlen = 50
    end,
    config = function()
        local orig_notify = vim.notify
        vim.notify = function(msg, level, opts)
            if level == vim.log.levels.WARN and msg:match("which%-key") then
                return
            end
            orig_notify(msg, level, opts)
        end



        local wk = require("which-key")

        wk.register({
            ["<leader>f"] = {
                name = "󰍉 Find",
                b = { group = "Buffers", icon = "󱦞" },
                c = { group = "Config", icon = "" },
                d = { group = "Directories", icon = "󰥨" },
                f = { group = "Files (current folder)", icon = "󰈞" },
                F = { group = "Files (system wide)", icon = "󰜏" },
                g = { group = "Grep (current buffer)", icon = "󰱼" },
                G = { group = "Grep (open buffers)", icon = "󱎸" },
                r = { group = "Recent Files", icon = "" },
                t = { group = "LaTeX Projects", icon = "" },
            },
        })
    end,
}
