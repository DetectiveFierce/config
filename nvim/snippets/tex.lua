local ls = require("luasnip")
local s = ls.snippet
local t = ls.text_node
local i = ls.insert_node

return {
    -- Fonts
    s({ trig = "`cal", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathcal{"), i(1), t("}") }),
    s({ trig = "`bb", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{"), i(1), t("}") }),
    s({ trig = "`frak", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathfrak{"), i(1), t("}") }),
    s({ trig = "`rm", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathrm{"), i(1), t("}") }),
    s({ trig = "`bf", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbf{"), i(1), t("}") }),
    s({ trig = "`sf", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathsf{"), i(1), t("}") }),
    s({ trig = "`tt", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathtt{"), i(1), t("}") }),
    s({ trig = "`it", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathit{"), i(1), t("}") }),

    -- Common symbols
    s({ trig = "`in", wordTrig = false, snippetType = "autosnippet" }, { t("\\in") }),
    s({ trig = "`ni", wordTrig = false, snippetType = "autosnippet" }, { t("\\ni") }),
    s({ trig = "`to", wordTrig = false, snippetType = "autosnippet" }, { t("\\to") }),
    s({ trig = "`map", wordTrig = false, snippetType = "autosnippet" }, { t("\\mapsto") }),
    s({ trig = "`iff", wordTrig = false, snippetType = "autosnippet" }, { t("\\iff") }),
    s({ trig = "`im", wordTrig = false, snippetType = "autosnippet" }, { t("\\implies") }),
    s({ trig = "`Ra", wordTrig = false, snippetType = "autosnippet" }, { t("\\Rightarrow") }),
    s({ trig = "`La", wordTrig = false, snippetType = "autosnippet" }, { t("\\Leftarrow") }),
    s({ trig = "`LR", wordTrig = false, snippetType = "autosnippet" }, { t("\\Leftrightarrow") }),
    s({ trig = "`int", wordTrig = false, snippetType = "autosnippet" }, { t("\\int "), i(1), t("\\,dx") }),
    s({ trig = "`sum", wordTrig = false, snippetType = "autosnippet" },
        { t("\\sum_{"), i(1, "i=1"), t("}^{"), i(2, "n"), t("}") }),
    s({ trig = "`prod", wordTrig = false, snippetType = "autosnippet" },
        { t("\\prod_{"), i(1, "i=1"), t("}^{"), i(2, "n"), t("}") }),

    -- Brackets and delimiters
    s({ trig = "`lr(", wordTrig = false, snippetType = "autosnippet" }, { t("\\left("), i(1), t("\\right)") }),
    s({ trig = "`lr[", wordTrig = false, snippetType = "autosnippet" }, { t("\\left["), i(1), t("\\right]") }),
    s({ trig = "`lr{", wordTrig = false, snippetType = "autosnippet" }, { t("\\left\\{"), i(1), t("\\right\\}") }),
    s({ trig = "`lr|", wordTrig = false, snippetType = "autosnippet" }, { t("\\left|"), i(1), t("\\right|") }),

    -- Logic
    s({ trig = "`land", wordTrig = false, snippetType = "autosnippet" }, { t("\\land") }),
    s({ trig = "`lor", wordTrig = false, snippetType = "autosnippet" }, { t("\\lor") }),
    s({ trig = "`lnot", wordTrig = false, snippetType = "autosnippet" }, { t("\\lnot") }),
    s({ trig = "`forall", wordTrig = false, snippetType = "autosnippet" }, { t("\\forall") }),
    s({ trig = "`exists", wordTrig = false, snippetType = "autosnippet" }, { t("\\exists") }),

    -- Sets
    s({ trig = "`N", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{N}") }),
    s({ trig = "`Z", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{Z}") }),
    s({ trig = "`Q", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{Q}") }),
    s({ trig = "`R", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{R}") }),
    s({ trig = "`C", wordTrig = false, snippetType = "autosnippet" }, { t("\\mathbb{C}") }),

    -- Greek letters
    s({ trig = "`a", wordTrig = false, snippetType = "autosnippet" }, { t("\\alpha") }),
    s({ trig = "`b", wordTrig = false, snippetType = "autosnippet" }, { t("\\beta") }),
    s({ trig = "`g", wordTrig = false, snippetType = "autosnippet" }, { t("\\gamma") }),
    s({ trig = "`G", wordTrig = false, snippetType = "autosnippet" }, { t("\\Gamma") }),
    s({ trig = "`d", wordTrig = false, snippetType = "autosnippet" }, { t("\\delta") }),
    s({ trig = "`D", wordTrig = false, snippetType = "autosnippet" }, { t("\\Delta") }),
    s({ trig = "`e", wordTrig = false, snippetType = "autosnippet" }, { t("\\epsilon") }),
    s({ trig = "`z", wordTrig = false, snippetType = "autosnippet" }, { t("\\zeta") }),
    s({ trig = "`l", wordTrig = false, snippetType = "autosnippet" }, { t("\\lambda") }),
    s({ trig = "`L", wordTrig = false, snippetType = "autosnippet" }, { t("\\Lambda") }),
    s({ trig = "`mu", wordTrig = false, snippetType = "autosnippet" }, { t("\\mu") }),
    s({ trig = "`s", wordTrig = false, snippetType = "autosnippet" }, { t("\\sigma") }),
    s({ trig = "`S", wordTrig = false, snippetType = "autosnippet" }, { t("\\Sigma") }),
    s({ trig = "`w", wordTrig = false, snippetType = "autosnippet" }, { t("\\omega") }),
    s({ trig = "`W", wordTrig = false, snippetType = "autosnippet" }, { t("\\Omega") }),

    -- Environments
    s({ trig = "`beg", wordTrig = false, snippetType = "autosnippet" }, {
        t("\\begin{"), i(1, "env"), t("}"), t({ "", "\t" }), i(2), t({ "", "\\end{" }), i(1), t("}"),
    }),
}
