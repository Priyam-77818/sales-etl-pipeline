"""
start_docker.py
===============
Step 4 — Checks Docker is running, then launches the full stack.

Usage:
    python start_docker.py            # start all services
    python start_docker.py --stop     # stop and remove containers
    python start_docker.py --status   # show container status
    python start_docker.py --logs     # tail logs from all services
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
import time

COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "docker-compose.yml")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def docker_available() -> bool:
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True, timeout=10
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def main():
    parser = argparse.ArgumentParser(description="Docker Compose helper")
    parser.add_argument("--stop",   action="store_true", help="Stop all containers")
    parser.add_argument("--status", action="store_true", help="Show container status")
    parser.add_argument("--logs",   action="store_true", help="Tail logs")
    parser.add_argument("--build",  action="store_true", default=True,
                        help="Rebuild images before starting (default: True)")
    args = parser.parse_args()

    # ── Check Docker ─────────────────────────────────────────────────────────
    if not docker_available():
        print("✗  Docker is not running or not installed.")
        print("   Download Docker Desktop from: https://www.docker.com/products/docker-desktop")
        print("   After installing, start Docker Desktop, then re-run this script.")
        sys.exit(1)

    print("✓  Docker is running\n")

    if args.stop:
        print("Stopping all containers...")
        run(["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"])
        print("✓  All containers stopped and volumes removed.")
        return

    if args.status:
        run(["docker", "compose", "-f", COMPOSE_FILE, "ps"])
        return

    if args.logs:
        run(["docker", "compose", "-f", COMPOSE_FILE, "logs", "--follow"])
        return

    # ── Start ─────────────────────────────────────────────────────────────────
    print("Starting sales-etl-pipeline stack...\n")
    cmd = ["docker", "compose", "-f", COMPOSE_FILE, "up", "--build", "-d"]
    run(cmd)

    print("\n" + "=" * 60)
    print("  Services starting up:")
    print("  ┌──────────────────────────────────────────────┐")
    print("  │  PostgreSQL    →  localhost:5432             │")
    print("  │  Airflow UI    →  http://localhost:8080      │")
    print("  │                   login: admin / admin       │")
    print("  │  ETL App       →  runs pipeline on start     │")
    print("  └──────────────────────────────────────────────┘")
    print("\n  Check status:  python start_docker.py --status")
    print("  View logs:     python start_docker.py --logs")
    print("  Stop all:      python start_docker.py --stop")
    print("=" * 60)


if __name__ == "__main__":
    main()
