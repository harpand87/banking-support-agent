import argparse
import json
import logging
import os

from app.orchestrator import BankingAgent
from app.knowledge import ChromaMiniLMEmbeddingProvider, ChromaSemanticRetriever, OpenAIEmbeddingProvider
from app.llm import GeminiModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Nontransactional banking support agent")
    parser.add_argument("question", nargs="?", help="user question")
    parser.add_argument("--session", default="default")
    parser.add_argument("--provider", choices=("offline", "gemini"), default="offline")
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--prompt-variant", choices=("minimal", "safety_contract", "evidence_first"), default="evidence_first")
    parser.add_argument("--retrieval", choices=("keyword", "semantic"), default="keyword")
    parser.add_argument("--semantic-provider", choices=("minilm", "openai"), default="minilm")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    question = args.question or input("Question: ")
    model = GeminiModel(model=args.model, prompt_variant=args.prompt_variant) if args.provider == "gemini" else None
    retriever = None
    if args.retrieval == "semantic":
        if args.semantic_provider == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                parser.error("OPENAI_API_KEY is required when --semantic-provider openai is selected")
            embeddings = OpenAIEmbeddingProvider()
        else:
            embeddings = ChromaMiniLMEmbeddingProvider()
        retriever = ChromaSemanticRetriever(embeddings=embeddings)
    response = BankingAgent(model=model, retriever=retriever).handle(question, args.session)
    print(json.dumps(response.as_dict(), indent=2))


if __name__ == "__main__":
    main()
