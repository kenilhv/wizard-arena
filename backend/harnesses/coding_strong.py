"""Strong coding harness — explicit contract + low temperature."""
class Harness:
    name = "Coder-Strong"

    def solve(self, spec: str, llm) -> str:
        return llm.chat(
            system=(
                "You are an expert Python programmer. Write clean, correct code "
                "that satisfies the spec exactly. Return ONLY Python source."
            ),
            user=f"Specification:\n{spec}\n\nImplement:",
            temperature=0.0,
            max_tokens=600,
        )
