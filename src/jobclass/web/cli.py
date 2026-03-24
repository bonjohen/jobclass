"""Command-line interface for the JobClass web application."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jobclass-web",
        description="JobClass labor market reporting website",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    import uvicorn

    uvicorn.run("jobclass.web.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
