vim.cmd("highlight clear")
vim.cmd("syntax reset")
vim.o.background = "dark"
vim.g.colors_name = "hate-of-nature"

local set = vim.api.nvim_set_hl

-- Core UI
set(0, 'Normal',          { fg = '#99cc58', bg = '#22350a' })
set(0, 'EndOfBuffer',     { fg = '#22350a', bg = '#22350a' })
set(0, 'Cursor',          { fg = '#22350a', bg = '#f4bf75' })
set(0, 'CursorLine',      { fg = '#99cc58', bg = '#4a6a1a' })
set(0, 'CursorColumn',    { fg = '#99cc58', bg = '#3a5412' })
set(0, 'CursorLineNr',    { fg = '#99cc58', bg = '#3a5412' })
set(0, 'LineNr',          { fg = '#162207', bg = '#22350a' })
set(0, 'SignColumn',      { fg = '#22350a', bg = '#1C2C09' })
set(0, 'StatusLine',      { fg = '#99cc58', bg = '#1C2C09' })
set(0, 'StatuslineNC',    { fg = '#99cc58', bg = '#1C2C09' })
set(0, 'VertSplit',       { fg = '#1C2C09', bg = '#1C2C09' })
set(0, 'WinSeparator',    { fg = '#1C2C09', bg = '#1C2C09' })
set(0, 'WildMenu',        { fg = '#22350a', bg = '#162207' })
set(0, "Pmenu",      { fg = "#99cc58", bg = "#1C2C09" })
set(0, "PmenuSel",   { fg = "#1C2C09", bg = "#99cc58", bold = true })
set(0, "PmenuSbar",  { bg = "#22350a" })
set(0, "PmenuThumb", { bg = "#5C842C" })
set(0, 'NormalFloat',     { fg = '#99cc58', bg = '#1C2C09' })
set(0, 'FloatBorder',     { fg = '#5C842C', bg = '#1C2C09' })
set(0, 'Directory',       { fg = '#5C842C' })
set(0, "NoNeckPainWidthUp",   {  fg = "#22350a", bg = "#22350a" })
set(0, "NoNeckPainWidthDown", {  fg = "#22350a", bg = "#22350a" })
-- Search and Matching
set(0, 'Search',          { fg = '#22350a', bg = '#f4bf75' })
set(0, 'IncSearch',       { fg = '#22350a', bg = '#f4bf75' })
set(0, 'CurSearch',       { fg = '#22350a', bg = '#f4bf75' })
set(0, 'MatchParen',      { fg = '#99cc58', bg = '#5C842C' })
set(0, 'Visual',          { fg = '#22350a', bg = '#5C842C' })

-- Folding
set(0, 'Folded',          { fg = '#99cc58', bg = '#2C460D' })
set(0, 'FoldColumn',      { fg = '#5C842C', bg = '#22350a' })

-- Diff
set(0, 'DiffAdd',         { fg = '#99cc58', bg = '#2C460D' })
set(0, 'DiffChange',      { fg = '#FD971F', bg = '#2C460D' })
set(0, 'DiffDelete',      { fg = '#f92626', bg = '#2C460D' })
set(0, 'DiffText',        { fg = '#A6E22E', bg = '#2C460D' })

-- Spelling
set(0, 'SpellBad',        { fg = '#f92626', bg = '#22350a', underline = true })
set(0, 'SpellCap',        { fg = '#66D9EF', bg = '#22350a', underline = true })
set(0, 'SpellRare',       { fg = '#AE81FF', bg = '#22350a', underline = true })
set(0, 'SpellLocal',      { fg = '#FD971F', bg = '#22350a', underline = true })

-- Syntax
set(0, 'Comment',         { fg = '#365610' })
set(0, 'NonText',         { fg = '#365610' })
set(0, 'Conceal',         { fg = '#365610', bg = '#22350a' })
set(0, 'Constant',        { fg = '#AE81FF' })
set(0, 'String',          { fg = '#f4bf75' })
set(0, 'Character',       { fg = '#f4bf75' })
set(0, 'Identifier',      { fg = '#99cc58' })
set(0, 'Statement',       { fg = '#F92672' })
set(0, 'Operator',        { fg = '#99cc58' })
set(0, 'Delimiter',       { fg = '#99cc58' })
set(0, 'PreProc',         { fg = '#FD971F' })
set(0, 'Type',            { fg = '#A6E22E' })
set(0, 'Function',        { fg = '#66D9EF' })
set(0, 'Special',         { fg = '#A6E22E' })
set(0, 'SpecialKey',      { fg = '#AE81FF' })
set(0, 'Underlined',      { fg = '#F92672' })
set(0, 'Todo',            { fg = '#66D9EF' })
set(0, 'Title',           { fg = '#A6E22E' })
set(0, 'MsgArea',         { fg = '#A6E22E' })
set(0, 'WarningMsg',      { fg = '#FD971F' })
set(0, 'Error',           { fg = '#f92626' })
set(0, 'ErrorMsg',        { fg = '#f92626' })

-- Diagnostics
set(0, 'DiagnosticInfo',           { fg = '#66D9EF' })
set(0, 'DiagnosticVirtualTextError', { fg = '#f92626', bg = '#2C1A1A' })
set(0, 'DiagnosticVirtualTextWarn',  { fg = '#FD971F', bg = '#2C260F' })
set(0, 'DiagnosticVirtualTextInfo',  { fg = '#66D9EF', bg = '#1A2C2C' })
set(0, 'DiagnosticVirtualTextHint',  { fg = '#AE81FF', bg = '#2C1F2C' })

-- LSP
set(0, 'LspInfoBorder', { fg = '#5C842C', bg = '#1C2C09' })

-- Telescope
set(0, "TelescopeNormal",        { fg = "#99cc58", bg = "#1C2C09" })
set(0, "TelescopeBorder",        { fg = "#5C842C", bg = "#1C2C09" })
set(0, "TelescopePromptNormal",  { fg = "#99cc58", bg = "#2C460D" })
set(0, "TelescopePromptBorder",  { fg = "#5C842C", bg = "#2C460D" })
set(0, "TelescopePromptPrefix",  { fg = "#FD971F", bg = "#2C460D" })
set(0, "TelescopeSelection",     { fg = "#22350a", bg = "#99cc58", bold = true })

-- Unselected tabs in the Vim tabline (top bar if using :tabnew)
set(0, "TabLine", { fg = "#5C842C", bg = "#1C2C09" })

-- Currently selected tab in the Vim tabline
set(0, "TabLineSel", { fg = "#22350a", bg = "#22350a", bold = true })

-- Background area in the tabline (padding behind tabs)
set(0, "TabLineFill", { fg = "#22350a", bg = "#0f1706" })

-- Unselected buffer tab (inactive buffer)
set(0, "BufferLineTab", { fg = "#5C842C", bg = "#192707" })

-- Selected buffer tab (active buffer)
set(0, "BufferLineTabSelected", { fg = "#22350a", bg = "#99cc58", bold = true })

-- Background behind the entire bufferline area (the empty space between or after tabs)
set(0, "BufferLineFill", { fg = "#365610", bg = "#0f1706" })

-- Separator between buffer tabs (unselected)
set(0, "BufferLineTabSeparator", { fg = "#22350a", bg = "#0f1706" })

-- Separator next to selected buffer tab
set(0, "BufferLineTabSeparatorSelected", { fg = "#22350a", bg = "#22350a" })

-- Thin line between each tab (non-tab-specific, default separator)
set(0, "BufferLineSeparator", { fg = "#22350a", bg = "#192707" })

-- Separator next to the selected buffer tab
set(0, "BufferLineSeparatorSelected", { fg = "#22350a", bg = "#1C2C09" })

-- Separator next to a visible (but not selected) tab (e.g. split view)
set(0, "BufferLineSeparatorVisible", { fg = "#22350a", bg = "#1C2C09" })

-- Thin separator between the "File Explorer" offset section and the first tab
set(0, "BufferLineOffsetSeparator", { fg = "#1C2C09", bg = "#1C2C09" })

-- The truncation indicator (e.g. `…`) at the edge of the bufferline when buffers overflow
set(0, "BufferLineTruncMarker", { fg = "#99cc58", bg = "#1C2C09" })

-- Separator used when grouping tabs (if using custom groups)
set(0, "BufferLineGroupSeparator", { fg = "#1C2C09", bg = "#1C2C09" })

-- Label text used to name a group of tabs (if using custom groups)
set(0, "BufferLineGroupLabel", { fg = "#1C2C09", bg = "#192707" })

-- The label shown in the offset area (e.g. “File Explorer” above NvimTree)
set(0, "BufferLineOffset", { fg = "#A6E22E", bg = "#1C2C09", bold = true })

-- Unselected close button
set(0, "BufferLineCloseButton", { fg = "#8c5151", bg = "#192707" })

-- Selected/hovered close button
set(0, "BufferLineCloseButtonSelected", { fg = "#ff5f5f", bg = "#22350a", bold = true })

-- Lazy.nvim Plugin UI
set(0, 'LazyNormal',        { fg = '#99cc58', bg = '#1C2C09' })
set(0, 'LazyH1',            { fg = '#A6E22E', bold = true })
set(0, 'LazyH2',            { fg = '#5C842C', bold = true })
set(0, 'LazyButton',        { fg = '#99cc58', bg = '#3a5412' })
set(0, 'LazyButtonActive',  { fg = '#22350a', bg = '#99cc58' })
set(0, 'LazyProgressDone',  { fg = '#A6E22E', bg = '#365610' })
set(0, 'LazyProgressTodo',  { fg = '#365610', bg = '#162207' })
set(0, 'LazySpecial',       { fg = '#A6E22E' })
set(0, 'LazyUrl',           { fg = '#5C842C', underline = true })

-- Mini.statusline modes
set(0, 'MiniStatuslineModeNormal',  { fg = '#99cc58', bg = '#22350a' })
set(0, 'MiniStatuslineModeInsert',  { fg = '#22350a', bg = '#99cc58' })
set(0, 'MiniStatuslineModeVisual',  { fg = '#22350a', bg = '#AE81FF' })
set(0, 'MiniStatuslineModeReplace', { fg = '#22350a', bg = '#FD971F' })
set(0, 'MiniStatuslineModeCommand', { fg = '#22350a', bg = '#F92672' })
set(0, 'MiniStatuslineModeOther',   { fg = '#22350a', bg = '#66D9EF' })

-- NvimTree file tree colors
set(0, "NvimTreeNormal",        { fg = "#99cc58", bg = "#1C2C09" })
set(0, "NvimTreeNormalNC",      { fg = "#99cc58", bg = "#1C2C09" })
set(0, "NvimTreeEndOfBuffer",   { fg = "#22350a", bg = "#1C2C09" })
set(0, "NvimTreeFolderName",    { fg = "#5C842C", bg = "#1C2C09" })
set(0, "NvimTreeRootFolder",    { fg = "#A6E22E", bold = true, bg = "#1C2C09" })
set(0, "NvimTreeVertSplit",     { fg = "#1C2C09", bg = "#1C2C09" })
set(0, "NvimTreeWinSeparator",  { fg = "#1C2C09", bg = "#1C2C09" })
set(0, "NvimTreeIndentMarker",  { fg = "#365610", bg = "#1C2C09" })
set(0, "NvimTreeCursorLine",    { fg = "#A6E22E", bg = "#365610", bold = true })
set(0, "NvimTreeTitle",         { fg = "#A6E22E", bg = "#1C2C09", bold = true })  -- added line
set(0, "NvimTreeLineNr",        { fg = "#365610", bg = "#1C2C09" }) -- absolute line numbers
set(0, "NvimTreeCursorLineNr",  { fg = "#A6E22E", bg = "#1C2C09", bold = true }) -- line number for selected line

set(0, "texCmd",              { fg = "#F92672" })
set(0, "texCmdAccent",        { fg = "#F92672" })
set(0, "texCmdLigature",      { fg = "#F92672" })
set(0, "texCmdGreek",         { fg = "#F92672" })
set(0, "texCmdMathEnv",       { fg = "#F92672" })
set(0, "texCmdEnvM",          { fg = "#F92672" })
set(0, "texCmdFootnote",      { fg = "#F92672" })
set(0, "texCmdConditional",   { fg = "#F92672" })
set(0, "texCmdConditionalINC",{ fg = "#F92672" })
set(0, "texCmdInput",         { fg = "#F92672" })
set(0, "texCmdBib",           { fg = "#F92672" })
set(0, "texCmdClass",         { fg = "#F92672" })
set(0, "texCmdPackage",       { fg = "#F92672" })
set(0, "texCmdNewthm",        { fg = "#F92672" })
set(0, "texCmdTitle",         { fg = "#F92672" })
set(0, "texCmdSize",          { fg = "#F92672" })
set(0, "texCmdStyle",         { fg = "#F92672" })
set(0, "texCmdStyleItal",     { fg = "#F92672" })
set(0, "texCmdStyleBold",     { fg = "#F92672" })
set(0, "texCmdStyleItalBold", { fg = "#F92672" })
set(0, "texCmdStyleBoldItal", { fg = "#F92672" })
set(0, "texCmdNewenv",        { fg = "#F92672" })
set(0, "texCmdDef",           { fg = "#F92672" })
set(0, "texCmdVerb",          { fg = "#F92672" })
set(0, "texCmdMinipage",      { fg = "#F92672" })
set(0, "texCmdParbox",        { fg = "#F92672" })
set(0, "texCmdE3",            { fg = "#F92672" })
set(0, "texCmdTodo",          { fg = "#F92672" })

-- Math (green)
set(0, "texMathSymbol",       { fg = "#A6E22E" })
set(0, "texMathGroup",        { fg = "#A6E22E" })
set(0, "texMathZone",         { fg = "#A6E22E" })
set(0, "texMathOper",         { fg = "#A6E22E" })
set(0, "texMathSuperSub",     { fg = "#A6E22E" })
set(0, "texMathDelim",        { fg = "#A6E22E" })
set(0, "texMathArg",          { fg = "#A6E22E" })
set(0, "texMathCmd",          { fg = "#A6E22E" })

-- Arguments (blue)
set(0, "texArg",              { fg = "#66D9EF" })
set(0, "texArgNew",           { fg = "#66D9EF" })
set(0, "texNewcmdArgName",    { fg = "#66D9EF" })
set(0, "texNewenvArgName",    { fg = "#66D9EF" })
set(0, "texNewthmArgName",    { fg = "#66D9EF" })
set(0, "texConditionalArg",   { fg = "#66D9EF" })
set(0, "texFileArg",          { fg = "#66D9EF" })
set(0, "texFilesArg",         { fg = "#66D9EF" })
set(0, "texTitleArg",         { fg = "#66D9EF" })
set(0, "texAuthorArg",        { fg = "#66D9EF" })
set(0, "texFootnoteArg",      { fg = "#66D9EF" })

-- Options (light green)
set(0, "texOpt",              { fg = "#99cc58" })
set(0, "texOptEqual",         { fg = "#99cc58" })
set(0, "texOptSep",           { fg = "#99cc58" })
set(0, "texFileOpt",          { fg = "#99cc58" })
set(0, "texFilesOpt",         { fg = "#99cc58" })
set(0, "texAuthorOpt",        { fg = "#99cc58" })
set(0, "texNewcmdOpt",        { fg = "#99cc58" })
set(0, "texNewenvOpt",        { fg = "#99cc58" })
set(0, "texNewthmOptCounter", { fg = "#99cc58" })
set(0, "texNewthmOptNumberby",{ fg = "#99cc58" })

-- Structure (purple)
set(0, "texBeginEnd",         { fg = "#AE81FF" })
set(0, "texSection",          { fg = "#AE81FF" })
set(0, "texGroup",            { fg = "#AE81FF" })
set(0, "texGroupError",       { fg = "#AE81FF" })
set(0, "texRefZone",          { fg = "#AE81FF" })

-- Delimiters (orange)
set(0, "texDelim",            { fg = "#FD971F" })
set(0, "texBasicDelimiter",   { fg = "#FD971F" })

-- Special characters (yellow)
set(0, "texSpecialChar",      { fg = "#f4bf75" })
set(0, "texLigature",         { fg = "#f4bf75" })
set(0, "texCmdSpaceCodeChar", { fg = "#f4bf75" })

-- Errors (red)
set(0, "texError",            { fg = "#f92626", bold = true })

-- Misc (gray)
set(0, "texComment",          { fg = "#365610" })
set(0, "texLength",           { fg = "#AE81FF" })
set(0, "texInputFile",        { fg = "#66D9EF" })

-- Linked Highlight Groups (examples)
vim.cmd [[
  hi! link MoreMsg SpecialKey
  hi! link MiniStatuslineDevinfo StatusLine
  hi! link MiniStatuslineFilename StatusLine
  hi! link MiniStatuslineFileinfo StatusLine
  hi! link MiniStatuslineInactive StatusLine
  hi! link Tabline NonText
  hi! link TermCursor Cursor
  hi! link MsgSeoarator StatusLine
  hi! link NormalFloat Pmenu
  hi! link FloatBorder WinSeparator
  hi! link ToolbarButton TabLineSel
  hi! link ToolbarLine TabLineFill
  hi link cssBraces Delimiter
  hi link cssClassName Special
  hi link cssClassNameDot icebergNormalFg
  hi link cssPseudoClassId Special
  hi link cssTagName Statement
  hi link helpHyperTextJump Constant
  hi link htmlArg Constant
  hi link htmlEndTag Statement
  hi link htmlTag Statement
  hi link jsonQuote icebergNormalFg
  hi link phpVarSelector Identifier
  hi link pythonFunction Title
  hi link rubyDefine Statement
  hi link rubyFunction Title
  hi link rubyInterpolationDelimiter String
  hi link rubySharpBang Comment
  hi link rubyStringDelimiter String
  hi link rustFuncCall icebergNormalFg
  hi link rustFuncName Title
  hi link rustType Constant
  hi link sassClass Special
  hi link shFunction icebergNormalFg
  hi link vimContinue Comment
  hi link vimFuncSID vimFunction
  hi link vimFuncVar icebergNormalFg
  hi link vimFunction Title
  hi link vimGroup Statement
  hi link vimHiGroup Statement
  hi link vimHiTerm Identifier
  hi link vimMapModKey Special
  hi link vimOption Identifier
  hi link vimVar icebergNormalFg
  hi link xmlAttrib Constant
  hi link xmlAttribPunct Statement
  hi link xmlEndTag Statement
  hi link xmlNamespace Statement
  hi link xmlTag Statement
  hi link xmlTagName Statement
  hi link yamlKeyValueDelimiter Delimiter
  hi link CtrlPPrtCursor Cursor
  hi link CtrlPMatch Title
  hi link CtrlPMode2 StatusLine
  hi link deniteMatched icebergNormalFg
  hi link deniteMatchedChar Title
  hi link elixirBlockDefinition Statement
  hi link elixirDefine Statement
  hi link elixirDocSigilDelimiter String
  hi link elixirDocTest String
  hi link elixirExUnitMacro Statement
  hi link elixirExceptionDefine Statement
  hi link elixirFunctionDeclaration Title
  hi link elixirKeyword Statement
  hi link elixirModuleDeclaration icebergNormalFg
  hi link elixirModuleDefine Statement
  hi link elixirPrivateDefine Statement
  hi link elixirStringDelimiter String
  hi link jsFlowMaybe icebergNormalFg
  hi link jsFlowObject icebergNormalFg
  hi link jsFlowType PreProc
  hi link graphqlName icebergNormalFg
  hi link graphqlOperator icebergNormalFg
  hi link gitmessengerHash Comment
  hi link gitmessengerHeader Statement
  hi link gitmessengerHistory Constant
  hi link jsArrowFunction Operator
  hi link jsClassDefinition icebergNormalFg
  hi link jsClassFuncName Title
  hi link jsExport Statement
  hi link jsFuncName Title
  hi link jsFutureKeys Statement
  hi link jsFuncCall icebergNormalFg
  hi link jsGlobalObjects Statement
  hi link jsModuleKeywords Statement
  hi link jsModuleOperators Statement
  hi link jsNull Constant
  hi link jsObjectFuncName Title
  hi link jsObjectKey Identifier
  hi link jsSuper Statement
  hi link jsTemplateBraces Special
  hi link jsUndefined Constant
  hi link markdownBold Special
  hi link markdownCode String
  hi link markdownCodeDelimiter String
  hi link markdownHeadingDelimiter Comment
  hi link markdownRule Comment
  hi link ngxDirective Statement
  hi link plug1 icebergNormalFg
  hi link plug2 Identifier
  hi link plugDash Comment
  hi link plugMessage Special
  hi link SignifySignAdd GitGutterAdd
  hi link SignifySignChange GitGutterChange
  hi link SignifySignChangeDelete GitGutterChangeDelete
  hi link SignifySignDelete GitGutterDelete
  hi link SignifySignDeleteFirstLine SignifySignDelete
  hi link StartifyBracket Comment
  hi link StartifyFile Identifier
  hi link StartifyFooter Constant
  hi link StartifyHeader Constant
  hi link StartifyNumber Special
  hi link StartifyPath Comment
  hi link StartifySection Statement
  hi link StartifySlash Comment
  hi link StartifySpecial icebergNormalFg
  hi link svssBraces Delimiter
  hi link swiftIdentifier icebergNormalFg
  hi link TSAttribute Special
  hi link TSBoolean Constant
  hi link TSCharacter Constant
  hi link TSComment Comment
  hi link TSConstructor icebergNormalFg
  hi link TSConditional Statement
  hi link TSConstant Constant
  hi link TSConstBuiltin Constant
  hi link TSConstMacro Constant
  hi link TSError Error
  hi link TSException Statement
  hi link TSField icebergNormalFg
  hi link TSFloat Constant
  hi link TSInclude Statement
  hi link TSKeyword Statement
  hi link TSKeywordFunction Function
  hi link TSLabel Special
  hi link TSNamespace Statement
  hi link TSNumber Constant
  hi link TSOperator icebergNormalFg
  hi link TSParameter icebergNormalFg
  hi link TSParameterReference icebergNormalFg
  hi link TSProperty icebergNormalFg
  hi link TSPunctDelimiter icebergNormalFg
  hi link TSPunctBracket icebergNormalFg
  hi link TSPunctSpecial Special
  hi link TSRepeat Statement
  hi link TSString String
  hi link TSStringRegex String
  hi link TSStringEscape Special
  hi link TSTag htmlTagName
  hi link TSTagAttribute htmlArg
  hi link TSTagDelimiter htmlTagName
  hi link TSText icebergNormalFg
  hi link TSTitle Title
  hi link TSType Type
  hi link TSTypeBuiltin Type
  hi link TSVariable icebergNormalFg
  hi link TSVariableBuiltin Statement
  hi link typescriptAjaxMethods icebergNormalFg
  hi link typescriptBraces icebergNormalFg
  hi link typescriptEndColons icebergNormalFg
  hi link typescriptFuncKeyword Statement
  hi link typescriptGlobalObjects Statement
  hi link typescriptHtmlElemProperties icebergNormalFg
  hi link typescriptIdentifier Statement
  hi link typescriptMessage icebergNormalFg
  hi link typescriptNull Constant
  hi link typescriptParens icebergNormalFg
]]
