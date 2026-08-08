return {
  "lervag/vimtex",
  ft = "tex",
  config = function()
    -- ╭────────────────────────────────────────────────────────────╮
    -- │                  VimTeX General Settings                    │
    -- ╰────────────────────────────────────────────────────────────╯
    vim.g.vimtex_syntax_enabled = 1
    vim.g.vimtex_view_method = "zathura"
    vim.g.vimtex_quickfix_mode = 0
    vim.g.vimtex_indent_enabled = 1
    vim.g.vimtex_mappings_enabled = 1
    vim.g.vimtex_imaps_enabled = 1
    vim.g.vimtex_complete_enabled = 1
    vim.g.vimtex_compiler_method = "latexmk"
    vim.g.vimtex_compiler_latexmk = {
       continuous = 1,
	options = {
        "-shell-escape",
        "-file-line-error",
        "-interaction=nonstopmode",
        "-synctex=1",
      },
    }

    -- Use SyncTeX with Zathura
 vim.g.vimtex_view_forward_options =
  "--synctex-forward @line:1:@tex --synctex-editor-command 'nvr --remote-silent +%{line} %{input}'"
    -- Folding
    vim.o.foldenable = false
    vim.o.foldmethod = "manual"
    vim.o.foldlevel = 99

    -- Register custom math environments
    vim.g.vimtex_syntax_custom_envs = {
	{ name = "UNequation", math = 1 },
    }

    vim.g.vimtex_syntax_custom_cmds = {
  { name = "UNsection", arg = 1 },
  { name = "UNsubsection", arg = 1 },
}
    -- ╭────────────────────────────────────────────────────────────╮
    -- │             VimTeX Highlight & TS Override Setup           │
    -- ╰────────────────────────────────────────────────────────────╯
vim.api.nvim_create_autocmd("FileType", {
  pattern = "tex",
  callback = function()
    -- Force Vim syntax and ensure Tree-sitter highlight is off

    vim.g.vimtex_envs_math = { 'UNequation' }
    -- Small delay to override Tree-sitter if it auto-attaches
    vim.defer_fn(function()
      vim.cmd("TSBufDisable highlight")
    end, 20)


    -- ╭────────────────────────────────────────────────────────────╮
    -- │       VimTeX Syntax Highlight Overrides (Ported Theme)     │
    -- ╰────────────────────────────────────────────────────────────╯
    local set = vim.api.nvim_set_hl
    set(0, 'texComment',           { fg = '#365610' })
    set(0, 'texCmdMathEnv',        {fg = '#f7f065'})
    set(0, 'texCmdEnv',            {fg = '#f7f065'})
    set(0, 'texBeginEnd',          { fg = '#f7f065'})
    set(0, 'texInputFile',         { fg = '#f7f065', italic = true })
    set(0, 'texSpecialChar',       { fg = '#f7f065' })
    set(0, 'texRefZone',           { fg = '#f7f065', italic = true })
    set(0, 'texArg',               { fg = '#f7f065'})
    set(0, 'texOnlyMath',          { fg = '#A6E22E' })
    set(0, 'texMathSymbol',        { fg = '#A6E22E' })
    set(0, 'texMathZone',          { fg = '#A6E22E' })
    set(0, 'texCmdGreek',          { fg = '#2ee249' } )
    set(0, 'texDelim',             { fg = '#AE81FF' })
    set(0, 'texCmd',               { fg = '#F92672' })
    set(0, 'texStatement',         { fg = '#F92672' })
    set(0, 'texSpecials',          { fg = '#F92672' })
    set(0, 'texMathEnvArgName',    { fg = '#FD971F' })
    set(0, 'texSection',           { fg = '#66D9EF', bold = true })
    set(0, 'texCUNsectionArg',     { fg = '#66D9EF', bold = true, italic=true })
    set(0, 'texCUNsubsectionArg',  { fg = '#66D9EF', bold = true, italic=true })
    set(0, 'texError',             { fg = '#f92626', bold = true })

end,
})

    -- ╭────────────────────────────────────────────────────────────╮
    -- │                      luasnip snippets                      │
    -- ╰────────────────────────────────────────────────────────────╯
    local present, ls = pcall(require, "luasnip")
    if present then
      local s = ls.snippet
      local t = ls.text_node
      local i = ls.insert_node
      local fmt = require("luasnip.extras.fmt").fmt

      ls.add_snippets("tex", {
        s("eq", fmt([[
          \begin{{equation}}
            {}
          \end{{equation}}
        ]], { i(1) })),

        s("fig", fmt([[
          \begin{{figure}}[htbp]
            \centering
            \includegraphics[width=0.8\textwidth]{{{}}}
            \caption{{{}}}
            \label{{fig:{}}}
          \end{{figure}}
        ]], { i(1, "path/to/image"), i(2, "caption text"), i(3, "label") })),

        s("sec", fmt([[
          \section{{{}}}
        ]], { i(1, "Section Title") })),
      })
    end
  end,
}
