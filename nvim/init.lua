-- Set colorscheme
vim.cmd.colorscheme("hate-of-nature")
vim.o.number = true
vim.g.mapleader = " "
vim.g.maplocalleader = ","


-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({
        "git", "clone", "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable", lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

-- Load all plugins defined in lua/plugins/*.lua
require("lazy").setup({ spec = { { import = "plugins" } } })

-- Load keybinds
require("keybinds")
