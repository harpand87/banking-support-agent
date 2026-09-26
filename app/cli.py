import argparse
import json
import logging

from app.orchestrator import BankingAgent
from app.knowledge import ChromaSemanticRetriever, OpenAIEmbeddingProvider
from app.llm import OpenAIModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Nontransactional banking support agent")
    parser.add_argument("question", nargs="?", help="user question")
    parser.add_argument("--session", default="default")
    parser.add_argument("--provider", choices=("offline", "openai"), default="offline")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--prompt-variant", choices=("minimal", "safety_contract", "evidence_first"), default="evidence_first")
    parser.add_argument("--retrieval", choices=("keyword", "semantic"), default="keyword")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    question = args.question or input("Question: ")
    model = OpenAIModel(model=args.model, prompt_variant=args.prompt_variant) if args.provider == "openai" else None
    retriever = ChromaSemanticRetriever(embeddings=OpenAIEmbeddingProvider()) if args.retrieval == "semantic" else None
    response = BankingAgent(model=model, retriever=retriever).handle(question, args.session)
    print(json.dumps(response.as_dict(), indent=2))


if __name__ == "__main__":
    main()
