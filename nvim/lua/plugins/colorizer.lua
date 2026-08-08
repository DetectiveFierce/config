return {
    "NvChad/nvim-colorizer.lua",
    config = function()
        require("colorizer").setup({ "*" }, {
            mode = "background",
            css = true,
            css_fn = true,
        })

        vim.defer_fn(function()
            for _, buf in ipairs(vim.api.nvim_list_bufs()) do
                if vim.api.nvim_buf_is_loaded(buf) then
                    require("colorizer").attach_to_buffer(buf)
                end
            end
        end, 0)
    end,
}
