; Generic fenced code block injection for standard markdown fences.
; Exclude plain `r`/`R` so we can route R chunks to the custom RChunk language.
((fenced_code_block
  (info_string
    (language) @injection.language)
  (code_fence_content) @injection.content)
 (#not-eq? @injection.language "r")
 (#not-eq? @injection.language "R"))

; R Markdown curly-brace chunk headers, e.g. ```{r}, ```{r setup, include=FALSE}
((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{[rR]([ ,].*)?\\}$")
 (#set! injection.language "RChunk"))

; Also treat plain fenced `r`/`R` blocks as R chunks in .Rmd.
((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^[rR]$")
 (#set! injection.language "RChunk"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{python([ ,].*)?\\}$")
 (#set! injection.language "python"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{julia([ ,].*)?\\}$")
 (#set! injection.language "julia"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{(bash|sh)([ ,].*)?\\}$")
 (#set! injection.language "bash"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{sql([ ,].*)?\\}$")
 (#set! injection.language "sql"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{dot([ ,].*)?\\}$")
 (#set! injection.language "dot"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{mermaid([ ,].*)?\\}$")
 (#set! injection.language "mermaid"))

((fenced_code_block
  (info_string) @_lang
  (code_fence_content) @injection.content)
 (#match? @_lang "^\\{(latex|tex)([ ,].*)?\\}$")
 (#set! injection.language "latex"))

((inline) @injection.content
 (#set! injection.language "markdown-inline"))

((html_block) @injection.content
 (#set! injection.language "html"))

((minus_metadata) @injection.content
 (#set! injection.language "yaml"))

((plus_metadata) @injection.content
 (#set! injection.language "toml"))
