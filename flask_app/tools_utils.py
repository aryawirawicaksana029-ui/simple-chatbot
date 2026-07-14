"""
tools_utils.py
Tool/function-calling implementations for ARIA — the actual Python functions
that run when the model requests a tool call, plus the JSON-schema tool
definitions sent to Groq so it knows these tools exist.

Two tools are provided:
- calculate: safe arithmetic evaluation. Parses the expression with Python's
  `ast` module and only ever executes numeric literals + basic operators —
  never eval(), which would let a cleverly-crafted expression run arbitrary
  Python. Same "don't trust text that reaches something executable" instinct
  as the RAG prompt-injection handling and the Markdown sanitization.
- web_search: DuckDuckGo's free Instant Answer API. No API key or signup
  needed, but it's built for quick factual/definition lookups ("what is X",
  "who is X") — it is NOT a general web search engine, so it often comes
  back empty for news, opinions, or anything needing a ranked list of pages.
"""

import ast
import operator

import requests

# ---------- Calculator ----------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    """
    Recursively evaluate an AST node, allowing ONLY numeric literals and the
    arithmetic operators above. Anything else — names, function calls,
    attribute access, imports, comprehensions, etc. — raises ValueError.
    This whitelist approach is what makes it safe to run on model/user-
    influenced input, unlike a plain eval(expression) call.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("expression may only contain numbers and + - * / % ** ( )")


def calculate(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression. Returns the result as a
    string, or a descriptive error message if the expression is invalid or
    contains anything other than numbers/operators."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: could not evaluate '{expression}' ({e})"


# ---------- Web search (DuckDuckGo Instant Answer API) ----------

def web_search(query: str) -> str:
    """
    Look up `query` via DuckDuckGo's free Instant Answer API. Returns a short
    text answer, or a message explaining that nothing was found (this API
    only covers factual/definition-style queries, not general web search).
    """
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return f"Error: web search failed ({e})"

    if data.get("AbstractText"):
        source = data.get("AbstractSource", "DuckDuckGo")
        return f"{data['AbstractText']} (Source: {source})"

    if data.get("Answer"):
        return data["Answer"]

    related = data.get("RelatedTopics", [])
    snippets = [t["Text"] for t in related if isinstance(t, dict) and t.get("Text")][:3]
    if snippets:
        return " | ".join(snippets)

    return (
        f"No quick answer found for '{query}'. DuckDuckGo's Instant Answer API "
        "works best for factual/definition queries, not general search or news."
    )


# ---------- Tool schema (sent to Groq) + dispatch table ----------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Evaluate a basic arithmetic expression (+, -, *, /, %, **, parentheses). "
                "Use this for any math instead of computing it yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate, e.g. '(12 + 8) * 3'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Look up a quick factual answer or definition on the web via DuckDuckGo. "
                "Best for 'what is X' / 'who is X' style questions. Not reliable for "
                "breaking news, prices, or opinion-based queries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "calculate": calculate,
    "web_search": web_search,
}