from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"
    os.chdir(data_dir)

    server = HTTPServer(("127.0.0.1", 8765), SimpleHTTPRequestHandler)
    print("Serving sample data at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
