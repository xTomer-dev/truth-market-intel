import app.ingestion  # noqa: F401
from app.ingestion.registry import registry


def main() -> None:
    for name in registry.list_sources():
        print(name)


if __name__ == "__main__":
    main()
