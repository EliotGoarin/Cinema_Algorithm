"""
Petit script utilitaire pour ingérer rapidement un catalogue de base.
Usage (depuis la racine) :
    python -m scripts.bootstrap --source popular --pages 10
"""

import argparse
from src.api.app import admin_bootstrap  # réutilise la logique de l'endpoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["popular", "trending"], default="popular")
    parser.add_argument("--pages", type=int, default=5)
    args = parser.parse_args()
    res = admin_bootstrap(source=args.source, pages=args.pages)
    print(res)
