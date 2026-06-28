"""Starter template for Coding Bench harness submissions."""
class Harness:
    name = "MyCodingHarness"

    def solve(self, spec: str, llm) -> str:
        return llm.chat(
            system=(
                "Write Python code for the task. Return ONLY valid Python — "
                "no markdown fences, no explanation."
            ),
            user=f"Task:\n{spec}\n\nPython solution:",
            temperature=0.0,
            max_tokens=512,
        )
