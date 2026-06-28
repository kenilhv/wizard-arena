"""Naive coding harness — dumps spec to LLM with weak instructions."""
class Harness:
    name = "Coder-Naive"

    def solve(self, spec: str, llm) -> str:
        return llm.chat("Write code.", spec, max_tokens=400)
