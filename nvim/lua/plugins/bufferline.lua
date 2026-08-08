return {
  "akinsho/bufferline.nvim",
  config = function()
    require("bufferline").setup({
      options = {
	buffer_close_icon = "✖",
        separator_style = "Thick",
        offsets = {
          {
            filetype = "NvimTree",
            text = "File Explorer",
            text_align = "center",
            separator = true,
          }
        },
        show_buffer_close_icons = true,
        show_close_icon = true,
        always_show_bufferline = true,
        diagnostics = "nvim_lsp",
      },
    })
  end,
}
