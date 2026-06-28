"""Starter template for Research Agent harness submissions."""
class Harness:
    name = "MyResearchHarness"

    def research(self, question: str, search, llm) -> str:
        # 1) Search the web for context (You.com)
        snippets = search.search(question, count=5)
        # 2) Ask the LLM to synthesize a concise answer
        return llm.chat(
            system="Answer factual questions using search results. Reply with ONLY the answer.",
            user=f"Question: {question}\n\nSearch results:\n{snippets}\n\nAnswer:",
            temperature=0.1,
            max_tokens=64,
        )
