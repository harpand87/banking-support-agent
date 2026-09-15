import argparse
import json
import logging

from app.orchestrator import BankingAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Nontransactional banking support agent")
    parser.add_argument("question", nargs="?", help="user question")
    parser.add_argument("--session", default="default")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    question = args.question or input("Question: ")
    response = BankingAgent().handle(question, args.session)
    print(json.dumps(response.as_dict(), indent=2))


if __name__ == "__main__":
    main()
