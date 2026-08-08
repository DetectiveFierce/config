-- ~/.config/nvim/lua/keybinds.lua

-- ╭────────────────────────────────────────────────────────────╮
-- │                      General Settings                       │
-- ╰────────────────────────────────────────────────────────────╯
local map = vim.keymap.set
local opts = { noremap = true, silent = true }

vim.o.mouse = "a"
vim.o.showtabline = 2

local wk = require("which-key")
local telescope = require("telescope.builtin")

-- ╭────────────────────────────────────────────────────────────╮
-- │                    Telescope Find Mappings                  │
-- ╰────────────────────────────────────────────────────────────╯
map("n", "<leader>fb", telescope.buffers, { desc = "Find buffer" })
map("n", "<leader>fc", function()
  telescope.find_files({ cwd = vim.fn.expand("~/.config") })
end, { desc = "Find config file" })
map("n", "<leader>fd", function()
  telescope.find_files({
    cwd = vim.fn.expand("~"),
    find_command = { "fd", "--type", "d", "--hidden", "--follow" },
  })
end, { desc = "Find directories (whole system)" })
map("n", "<leader>ff", telescope.find_files, { desc = "Find files (current folder)" })
map("n", "<leader>fF", function()
  telescope.find_files({ cwd = "/" })
end, { desc = "Find files (whole system)" })
map("n", "<leader>fg", telescope.current_buffer_fuzzy_find, { desc = "Grep text (current buffer)" })
map("n", "<leader>fG", telescope.live_grep, { desc = "Grep text (open buffers)" })
map("n", "<leader>fr", telescope.oldfiles, { desc = "Recently open files" })
map("n", "<leader>ft", function()
  telescope.find_files({
    cwd = vim.fn.expand("~/Landing Zone/Latex Projects"),
    find_command = { "fd", "--type", "d", "--hidden", "--follow" },
  })
end, { desc = " Find LaTeX Projects" })

wk.register({
  f = {
    name = "Find",
    b = "Find buffer",
    c = "Find config file",
    d = "Find directories",
    f = "Find files (current folder)",
    F = "Find files (system-wide)",
    g = "Grep in buffer",
    G = "Live grep",
    r = "Recently opened files",
    t = "Find LaTeX Projects",
  },
}, { prefix = "<leader>" })

-- ╭────────────────────────────────────────────────────────────╮
-- │                    Global Utility Mappings                  │
-- ╰────────────────────────────────────────────────────────────╯
map("n", "<leader>w", ":w<CR>", { desc = "Write file" })
map("n", "<leader>q", ":q<CR>", { desc = "Quit" })
map("n", "<leader>Q", ":qall<CR>", { desc = "Close all buffers" })
map("n", "<leader>h", ":nohlsearch<CR>", { desc = "Clear search highlight" })
map("n", "<leader>e", ":NvimTreeToggle<CR>", { desc = "Toggle file explorer" })
map("n", "<leader>r", ":so $MYVIMRC<CR>", { desc = "Reload config" })
map("n", "<leader>n", ":enew<CR>", { desc = "New file" })
map('n','<A-j>',':m .+1<CR>==', { silent = true })
map('n','<A-k>',':m .-2<CR>==', { silent = true })
map("n", "<Space>z", function()
  require("no-neck-pain").toggle()
end, { desc = "Toggle Centered Layout" })

wk.register({
  w = "Write file",
  q = "Quit",
  Q = "Close all buffers",
  h = "Clear search highlight",
  e = "Toggle file explorer",
  r = "Reload config",
  n = "New file",
}, { prefix = "<leader>" })

-- ╭────────────────────────────────────────────────────────────╮
-- │                  Split Navigation Mappings                  │
-- ╰────────────────────────────────────────────────────────────╯
map("n", "<C-h>", "<C-w>h", opts)
map("n", "<C-j>", "<C-w>j", opts)
map("n", "<C-k>", "<C-w>k", opts)
map("n", "<C-l>", "<C-w>l", opts)

-- ╭────────────────────────────────────────────────────────────╮
-- │                   Clipboard and Save Mappings               │
-- ╰────────────────────────────────────────────────────────────╯
map("v", "<C-c>", '"+y', { noremap = true, silent = true, desc = "Copy to system clipboard" })
map("n", "<C-s>", ":w<CR>:VimtexCompile<CR>", { desc = "Save and Compile" })

-- ╭────────────────────────────────────────────────────────────╮
-- │                    Colorscheme + Reload Commands            │
-- ╰────────────────────────────────────────────────────────────╯
vim.api.nvim_create_user_command("ReloadTheme", function()
  vim.cmd("colorscheme hate-of-nature")
  vim.api.nvim_exec_autocmds("ColorScheme", { pattern = "*" })
end, {})

vim.api.nvim_create_user_command("ReloadConfig", function()
  for name,_ in pairs(package.loaded) do
    if name:match("^user") or name:match("^plugins") or name:match("^keybinds") or name:match("^colors") then
      package.loaded[name] = nil
    end
  end
  dofile(vim.fn.stdpath("config") .. "/init.lua")
  print("✅ Neovim config reloaded")
end, {})

vim.api.nvim_create_user_command("Reload", function()
  vim.cmd("ReloadConfig")
  vim.cmd("colorscheme hate-of-nature")
  vim.api.nvim_exec_autocmds("ColorScheme", { pattern = "*" })
  print("🎨 Theme and config reloaded")
end, {})

-- ╭────────────────────────────────────────────────────────────╮
-- │                 VimTeX LaTeX Keymaps (which-key)           │
-- ╰────────────────────────────────────────────────────────────╯
vim.api.nvim_create_autocmd("FileType", {
  pattern = "tex",
  callback = function()
    local opts = { buffer = true, silent = true }

    map("n", "<leader>ll", "<cmd>VimtexCompile<CR>",  vim.tbl_extend("force", opts, { desc = "Compile LaTeX" }))
    map("n", "<leader>lv", "<cmd>VimtexView<CR>",     vim.tbl_extend("force", opts, { desc = "View PDF" }))
    map("n", "<leader>lc", "<cmd>VimtexClean<CR>",    vim.tbl_extend("force", opts, { desc = "Clean build files" }))
    map("n", "<leader>lt", "<cmd>VimtexTocToggle<CR>",vim.tbl_extend("force", opts, { desc = "Toggle TOC" }))
    map("n", "<leader>le", "<cmd>VimtexErrors<CR>",   vim.tbl_extend("force", opts, { desc = "Open error list" }))
    map("n", "<leader>ls", "<cmd>VimtexStatus<CR>",   vim.tbl_extend("force", opts, { desc = "VimTeX status" }))

    map("n", "<leader>lp", function()
      vim.g.vimtex_view_forward_options = "--synctex-forward @line:@col:@tex --no-highlight"
      vim.cmd("VimtexView")
    end, vim.tbl_extend("force", opts, { desc = "View PDF (quiet jump)" }))

    map("n", "<leader>lP", function()
      vim.g.vimtex_view_forward_options = "--synctex-forward @line:@col:@tex"
      vim.cmd("VimtexView")
    end, vim.tbl_extend("force", opts, { desc = "View PDF (highlight jump)" }))

    wk.register({
      l = {
        name = "LaTeX",
        l = "Compile LaTeX",
        v = "View PDF",
        c = "Clean build files",
        t = "Toggle TOC",
        e = "Open error list",
        s = "VimTeX status",
        p = "View PDF (quiet jump)",
        P = "View PDF (highlight jump)",
      },
    }, { prefix = "<leader>", buffer = 0 })
  end,
})

vim.keymap.set("n", "<C-s>", function()
  vim.cmd("w")              -- save
  vim.cmd("VimtexCompile")  -- compile LaTeX
end, { desc = "Save and compile LaTeX", silent = true })
