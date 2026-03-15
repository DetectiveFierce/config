[
  (paragraph)
  (indented_code_block)
  (pipe_table)
] @text

; Capture fenced chunk bodies so themes can apply a distinct background.
(fenced_code_block
  (code_fence_content) @embedded)

; Also capture entire fenced blocks so delimiters/background are consistently styled.
(fenced_code_block) @embedded

; More specific capture for optional theme targeting.
(fenced_code_block
  (code_fence_content) @embedded.rmd_chunk)

(fenced_code_block) @embedded.rmd_chunk

[
  (atx_heading)
  (setext_heading)
  (thematic_break)
] @title.markup
(setext_heading (paragraph) @title.markup)

[
  (list_marker_plus)
  (list_marker_minus)
  (list_marker_star)
  (list_marker_dot)
  (list_marker_parenthesis)
] @punctuation.list_marker.markup

(block_quote_marker) @punctuation.markup
(pipe_table_header "|" @punctuation.markup)
(pipe_table_row "|" @punctuation.markup)
(pipe_table_delimiter_row "|" @punctuation.markup)
(pipe_table_delimiter_cell "-" @punctuation.markup)

[
  (fenced_code_block_delimiter)
  (info_string)
] @punctuation.embedded.markup.rmd_chunk

(link_reference_definition) @link_text.markup
(link_destination) @link_uri.markup
