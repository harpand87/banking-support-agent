from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeItem:
    source: str
    title: str
    text: str
    topics: tuple[str, ...]


KNOWLEDGE = (
    KnowledgeItem("KB-001", "Everyday Account", "The Everyday Account has no monthly maintenance fee. Standard overdraft and external transfer policies may apply.", ("everyday", "fee", "account")),
    KnowledgeItem("KB-002", "Student Account", "The Student Account is intended for eligible students. Applicants may be asked for proof of current enrollment through an official channel.", ("student", "eligibility", "documents")),
    KnowledgeItem("KB-003", "Dispute Support", "For a suspected unauthorized transaction, contact the official fraud or dispute team promptly through an authenticated bank channel. Do not share passwords or one-time codes.", ("fraud", "dispute", "security")),
    KnowledgeItem("KB-004", "Budgeting Education", "A simple budgeting example can divide take-home income into needs, savings, and discretionary spending. This is educational information, not individualized financial advice.", ("budget", "education", "advice")),
)

STOPWORDS = {"what", "how", "the", "for", "and", "does", "not", "that", "this", "with", "from", "may"}


def search(query: str, limit: int = 3) -> list[KnowledgeItem]:
    terms = {term.lower().strip("?!.,") for term in query.split() if len(term) > 2 and term.lower() not in STOPWORDS}
    scored = []
    for item in KNOWLEDGE:
        haystack = f"{item.title} {item.text} {' '.join(item.topics)}".lower()
        score = sum(term in haystack for term in terms)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda value: value[0], reverse=True)
    if not scored:
        return []
    best_score = scored[0][0]
    return [item for score, item in scored if score == best_score][:limit]
