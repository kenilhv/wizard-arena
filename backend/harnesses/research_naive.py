"""Naive research harness — one search, minimal prompt."""
class Harness:
    name = "Search-Naive"

    def research(self, question: str, search, llm) -> str:
        snippets = search.search(question)
        return llm.chat("Answer the question.", f"Q: {question}\n{snippets}")
