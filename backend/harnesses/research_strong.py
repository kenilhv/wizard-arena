"""Strong research harness — refined query + structured synthesis."""
class Harness:
    name = "Search-Strong"

    def research(self, question: str, search, llm) -> str:
        snippets = search.search(question + " facts", count=8)
        return llm.chat(
            system=(
                "You are a precise research agent. Use search results to answer "
                "factual questions. Include key terms from sources. Reply with ONLY the answer."
            ),
            user=f"Question: {question}\n\nSources:\n{snippets}\n\nConcise answer:",
            temperature=0.0,
            max_tokens=48,
        )
