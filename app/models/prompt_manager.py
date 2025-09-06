from dataclasses import dataclass


@dataclass
class PromptManager:
    simplify_template: str = (
        "You are a legal document simplifier. Rewrite the text in plain language, keeping meaning.\n"
        "If language is not English, translate into the requested language.\n"
        "Text:\n{content}\n\nPlain-language version:"
    )
    risk_template: str = (
        "You are a legal risk detector. Identify risky clauses, assign severity (low/medium/high), and suggest actions.\n"
        "Return concise explanations.\nText:\n{content}\n\nRisks:"
    )
    clause_template: str = (
        "Break down the document clause-by-clause. For each clause provide a short explanation.\nText:\n{content}\n\nClauses:"
    )
    translate_template: str = (
        "Translate the text into {language} in plain language appropriate for non-experts.\nText:\n{content}\n\nTranslation:"
    )

    def build(self, task: str, content: str, language: str = "en") -> str:
        if task == "risk":
            return self.risk_template.format(content=content)
        if task == "summarize":
            return self.clause_template.format(content=content)
        if task == "translate":
            return self.translate_template.format(content=content, language=language)
        return self.simplify_template.format(content=content)
