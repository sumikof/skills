#!/usr/bin/env python3
"""domain別の最終取得日時を確認するスクリプト"""

import argparse
import os
import sqlite3


def check_fetch_time(db_path: str, domain: str) -> str | None:
    """domain_fetch_logから最終取得日時を返す。未取得またはDB/テーブル未作成の場合はNone。"""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT fetched_at FROM domain_fetch_log WHERE domain = ?", (domain,)
        ).fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.OperationalError:
        # テーブルが存在しない場合
        return None


def main():
    parser = argparse.ArgumentParser(description="domain別の最終取得日時を確認")
    parser.add_argument("domain", help="確認するdomain名")
    parser.add_argument("--db", default="finance-rate.db", help="SQLiteファイルパス（デフォルト: finance-rate.db）")
    args = parser.parse_args()

    fetched_at = check_fetch_time(args.db, args.domain)
    if fetched_at is None:
        print(f"[{args.domain}] 未取得")
    else:
        print(f"[{args.domain}] 最終取得: {fetched_at}")


if __name__ == "__main__":
    main()
