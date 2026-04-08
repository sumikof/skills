#!/usr/bin/env python3
"""
re_db.py - リバースエンジニアリング解析用SQLite管理CLI

複数の並列エージェントが共通のDBを通じて解析結果を共有・蓄積する。
コンテキストを汚染しないよう、出力は常にコンパクトに保つ。

使い方:
  python re_db.py init --db .re_analysis.db
  python re_db.py session create --repo-path /path/to/repo --repo-name myapp
  python re_db.py step claim --session-id 1 --phase 2 --agent-id agent_routing
  python re_db.py step done --session-id 1 --phase 2 --step routing --summary "24エンドポイント発見"
  python re_db.py endpoint add --session-id 1 --json '{"method":"GET","path":"/api/users"}'
  python re_db.py context summary --session-id 1
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# DB接続ユーティリティ
# ---------------------------------------------------------------------------

def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 並列書き込みに対応
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# スキーマ定義
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path    TEXT NOT NULL UNIQUE,
    repo_name    TEXT NOT NULL,
    status       TEXT DEFAULT 'in_progress',
    tech_stack   TEXT,
    project_type TEXT,
    arch_pattern TEXT,
    entry_points TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analysis_steps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES analysis_sessions(id),
    phase        INTEGER NOT NULL,
    step_name    TEXT NOT NULL,
    status       TEXT DEFAULT 'pending',
    agent_id     TEXT,
    claimed_at   TEXT,
    summary      TEXT,
    completed_at TEXT,
    UNIQUE(session_id, phase, step_name)
);

CREATE TABLE IF NOT EXISTS scanned_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES analysis_sessions(id),
    file_path       TEXT NOT NULL,
    file_category   TEXT,
    content_summary TEXT,
    key_elements    TEXT,
    scanned_by      TEXT,
    analyzed_at     TEXT DEFAULT (datetime('now')),
    UNIQUE(session_id, file_path)
);

CREATE TABLE IF NOT EXISTS endpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES analysis_sessions(id),
    method          TEXT NOT NULL,
    path            TEXT NOT NULL,
    description     TEXT,
    handler_file    TEXT,
    handler_func    TEXT,
    auth_required   INTEGER DEFAULT 0,
    path_params     TEXT,
    query_params    TEXT,
    request_body    TEXT,
    response_body   TEXT,
    response_status INTEGER DEFAULT 200,
    domain_name     TEXT,
    UNIQUE(session_id, method, path)
);

CREATE TABLE IF NOT EXISTS data_models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES analysis_sessions(id),
    model_name  TEXT NOT NULL,
    table_name  TEXT,
    source_file TEXT,
    description TEXT,
    fields      TEXT,
    relations   TEXT,
    indexes     TEXT,
    domain_name TEXT,
    UNIQUE(session_id, model_name)
);

CREATE TABLE IF NOT EXISTS functional_domains (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         INTEGER NOT NULL REFERENCES analysis_sessions(id),
    domain_name        TEXT NOT NULL,
    description        TEXT,
    screens            TEXT,
    screen_transitions TEXT,
    business_rules     TEXT,
    UNIQUE(session_id, domain_name)
);

CREATE TABLE IF NOT EXISTS architecture_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES analysis_sessions(id),
    category   TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

# Phase別のデフォルトステップ定義
DEFAULT_STEPS = {
    1: ["config_files", "dir_structure", "readme", "entry_points"],
    2: ["architecture", "routing", "data_models", "frontend", "domains"],
    3: ["readme_doc", "system_overview", "api_doc", "data_model_doc", "feature_docs"],
}


# ---------------------------------------------------------------------------
# コマンド: init
# ---------------------------------------------------------------------------

def cmd_init(args):
    conn = get_db(args.db)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"OK: DB initialized at {args.db}")


# ---------------------------------------------------------------------------
# コマンド: session
# ---------------------------------------------------------------------------

def cmd_session(args):
    conn = get_db(args.db)

    if args.action == "create":
        try:
            cur = conn.execute(
                "INSERT INTO analysis_sessions (repo_path, repo_name) VALUES (?, ?)",
                (args.repo_path, args.repo_name),
            )
            session_id = cur.lastrowid
            # デフォルトステップを登録
            for phase, steps in DEFAULT_STEPS.items():
                for step in steps:
                    conn.execute(
                        "INSERT OR IGNORE INTO analysis_steps (session_id, phase, step_name) VALUES (?,?,?)",
                        (session_id, phase, step),
                    )
            conn.commit()
            print(json.dumps({"session_id": session_id, "is_new": True, "status": "in_progress"}))
        except sqlite3.IntegrityError:
            row = conn.execute(
                "SELECT id, status FROM analysis_sessions WHERE repo_path=?", (args.repo_path,)
            ).fetchone()
            print(json.dumps({"session_id": row["id"], "is_new": False, "status": row["status"]}))

    elif args.action == "get":
        row = conn.execute(
            "SELECT * FROM analysis_sessions WHERE repo_path=?", (args.repo_path,)
        ).fetchone()
        if row:
            print(json.dumps(dict(row)))
        else:
            print(json.dumps(None))

    elif args.action == "update":
        conn.execute(
            "UPDATE analysis_sessions SET status=?, updated_at=? WHERE id=?",
            (args.status, now(), args.session_id),
        )
        conn.commit()
        print(f"OK: session {args.session_id} status={args.status}")

    elif args.action == "set-meta":
        fields, vals = [], []
        if args.tech_stack:
            fields.append("tech_stack=?"); vals.append(args.tech_stack)
        if args.project_type:
            fields.append("project_type=?"); vals.append(args.project_type)
        if args.arch_pattern:
            fields.append("arch_pattern=?"); vals.append(args.arch_pattern)
        if args.entry_points:
            fields.append("entry_points=?"); vals.append(args.entry_points)
        if fields:
            fields.append("updated_at=?"); vals.append(now())
            vals.append(args.session_id)
            conn.execute(f"UPDATE analysis_sessions SET {', '.join(fields)} WHERE id=?", vals)
            conn.commit()
        print(f"OK: session {args.session_id} metadata updated")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: step
# ---------------------------------------------------------------------------

def cmd_step(args):
    conn = get_db(args.db)

    if args.action == "claim":
        # 原子的にpendingなステップをclaimする（並列エージェントの競合を防ぐ）
        with conn:
            row = conn.execute(
                """SELECT id, step_name FROM analysis_steps
                   WHERE session_id=? AND phase=? AND status='pending'
                   ORDER BY id LIMIT 1""",
                (args.session_id, args.phase),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE analysis_steps SET status='claimed', agent_id=?, claimed_at=? WHERE id=?",
                    (args.agent_id, now(), row["id"]),
                )
                print(json.dumps({"claimed": True, "step_name": row["step_name"], "step_id": row["id"]}))
            else:
                print(json.dumps({"claimed": False}))

    elif args.action == "done":
        conn.execute(
            """UPDATE analysis_steps
               SET status='completed', summary=?, completed_at=?, agent_id=COALESCE(agent_id, ?)
               WHERE session_id=? AND phase=? AND step_name=?""",
            (args.summary, now(), getattr(args, "agent_id", None),
             args.session_id, args.phase, args.step),
        )
        conn.commit()
        print(f"OK: phase={args.phase} step={args.step} completed")

    elif args.action == "skip":
        conn.execute(
            "UPDATE analysis_steps SET status='skipped', completed_at=? WHERE session_id=? AND phase=? AND step_name=?",
            (now(), args.session_id, args.phase, args.step),
        )
        conn.commit()
        print(f"OK: phase={args.phase} step={args.step} skipped")

    elif args.action == "list":
        rows = conn.execute(
            "SELECT phase, step_name, status, agent_id, summary FROM analysis_steps WHERE session_id=? ORDER BY phase, id",
            (args.session_id,),
        ).fetchall()
        lines = ["Phase  Step            Status     Agent          Summary"]
        lines.append("-" * 70)
        for r in rows:
            summary = (r["summary"] or "")[:30]
            lines.append(f"  {r['phase']}    {r['step_name']:<16}{r['status']:<11}{(r['agent_id'] or ''):<15}{summary}")
        print("\n".join(lines))

    elif args.action == "pending":
        rows = conn.execute(
            "SELECT phase, step_name FROM analysis_steps WHERE session_id=? AND status='pending' ORDER BY phase, id",
            (args.session_id,),
        ).fetchall()
        print(json.dumps([{"phase": r["phase"], "step": r["step_name"]} for r in rows]))

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: file
# ---------------------------------------------------------------------------

def cmd_file(args):
    conn = get_db(args.db)

    if args.action == "add":
        key_elements = args.key_elements or "{}"
        conn.execute(
            """INSERT OR REPLACE INTO scanned_files
               (session_id, file_path, file_category, content_summary, key_elements, scanned_by)
               VALUES (?,?,?,?,?,?)""",
            (args.session_id, args.path, args.category, args.summary, key_elements, getattr(args, "agent_id", None)),
        )
        conn.commit()
        print(f"OK: file recorded {args.path}")

    elif args.action == "exists":
        row = conn.execute(
            "SELECT id FROM scanned_files WHERE session_id=? AND file_path=?",
            (args.session_id, args.path),
        ).fetchone()
        print(json.dumps({"exists": row is not None}))

    elif args.action == "list":
        rows = conn.execute(
            "SELECT file_path, file_category, content_summary FROM scanned_files WHERE session_id=? ORDER BY file_category, file_path",
            (args.session_id,),
        ).fetchall()
        for r in rows:
            cat = (r["file_category"] or "other").ljust(12)
            summary = (r["content_summary"] or "")[:60]
            print(f"[{cat}] {r['file_path']}: {summary}")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: endpoint
# ---------------------------------------------------------------------------

def cmd_endpoint(args):
    conn = get_db(args.db)

    if args.action == "add":
        data = json.loads(args.json)
        conn.execute(
            """INSERT OR REPLACE INTO endpoints
               (session_id, method, path, description, handler_file, handler_func,
                auth_required, path_params, query_params, request_body, response_body,
                response_status, domain_name)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                args.session_id,
                data.get("method", "GET"),
                data["path"],
                data.get("description"),
                data.get("handler_file"),
                data.get("handler_func"),
                int(data.get("auth_required", 0)),
                json.dumps(data["path_params"]) if "path_params" in data else None,
                json.dumps(data["query_params"]) if "query_params" in data else None,
                data.get("request_body"),
                data.get("response_body"),
                data.get("response_status", 200),
                data.get("domain_name"),
            ),
        )
        conn.commit()
        print(f"OK: endpoint {data.get('method','GET')} {data['path']}")

    elif args.action == "list":
        where = "WHERE session_id=?"
        params = [args.session_id]
        if getattr(args, "domain", None):
            where += " AND domain_name=?"; params.append(args.domain)
        rows = conn.execute(
            f"SELECT method, path, description, auth_required, domain_name FROM endpoints {where} ORDER BY path",
            params,
        ).fetchall()
        print(f"{'METHOD':<8} {'PATH':<45} {'AUTH':<5} {'DOMAIN':<15} DESC")
        print("-" * 90)
        for r in rows:
            auth = "Y" if r["auth_required"] else "N"
            desc = (r["description"] or "")[:30]
            domain = (r["domain_name"] or "")[:15]
            print(f"{r['method']:<8} {r['path']:<45} {auth:<5} {domain:<15} {desc}")
        print(f"\n合計: {len(rows)}件")

    elif args.action == "set-domain":
        conn.execute(
            "UPDATE endpoints SET domain_name=? WHERE session_id=? AND method=? AND path=?",
            (args.domain, args.session_id, args.method, args.path),
        )
        conn.commit()
        print(f"OK: {args.method} {args.path} → domain={args.domain}")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: model
# ---------------------------------------------------------------------------

def cmd_model(args):
    conn = get_db(args.db)

    if args.action == "add":
        data = json.loads(args.json)
        conn.execute(
            """INSERT OR REPLACE INTO data_models
               (session_id, model_name, table_name, source_file, description,
                fields, relations, indexes, domain_name)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                args.session_id,
                data["model_name"],
                data.get("table_name"),
                data.get("source_file"),
                data.get("description"),
                json.dumps(data["fields"]) if "fields" in data else None,
                json.dumps(data["relations"]) if "relations" in data else None,
                json.dumps(data["indexes"]) if "indexes" in data else None,
                data.get("domain_name"),
            ),
        )
        conn.commit()
        print(f"OK: model {data['model_name']}")

    elif args.action == "list":
        rows = conn.execute(
            "SELECT model_name, table_name, source_file, description, domain_name FROM data_models WHERE session_id=? ORDER BY model_name",
            (args.session_id,),
        ).fetchall()
        print(f"{'MODEL':<25} {'TABLE':<25} {'DOMAIN':<15} DESC")
        print("-" * 80)
        for r in rows:
            desc = (r["description"] or "")[:25]
            domain = (r["domain_name"] or "")[:15]
            print(f"{r['model_name']:<25} {(r['table_name'] or ''):<25} {domain:<15} {desc}")
        print(f"\n合計: {len(rows)}件")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: domain
# ---------------------------------------------------------------------------

def cmd_domain(args):
    conn = get_db(args.db)

    if args.action == "add":
        data = json.loads(args.json) if getattr(args, "json", None) else {}
        conn.execute(
            """INSERT OR REPLACE INTO functional_domains
               (session_id, domain_name, description, screens, screen_transitions, business_rules)
               VALUES (?,?,?,?,?,?)""",
            (
                args.session_id,
                args.name,
                args.desc or data.get("description"),
                json.dumps(data["screens"]) if "screens" in data else None,
                json.dumps(data["screen_transitions"]) if "screen_transitions" in data else None,
                json.dumps(data["business_rules"]) if "business_rules" in data else None,
            ),
        )
        conn.commit()
        print(f"OK: domain {args.name}")

    elif args.action == "update":
        data = json.loads(args.json)
        fields, vals = [], []
        for col in ("description", "screens", "screen_transitions", "business_rules"):
            if col in data:
                fields.append(f"{col}=?")
                vals.append(json.dumps(data[col]) if isinstance(data[col], (list, dict)) else data[col])
        if fields:
            vals.extend([args.session_id, args.name])
            conn.execute(
                f"UPDATE functional_domains SET {', '.join(fields)} WHERE session_id=? AND domain_name=?",
                vals,
            )
            conn.commit()
        print(f"OK: domain {args.name} updated")

    elif args.action == "list":
        rows = conn.execute(
            "SELECT domain_name, description FROM functional_domains WHERE session_id=? ORDER BY domain_name",
            (args.session_id,),
        ).fetchall()
        for r in rows:
            desc = (r["description"] or "")[:60]
            print(f"  {r['domain_name']}: {desc}")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: note
# ---------------------------------------------------------------------------

def cmd_note(args):
    conn = get_db(args.db)

    if args.action == "add":
        conn.execute(
            "INSERT INTO architecture_notes (session_id, category, title, content) VALUES (?,?,?,?)",
            (args.session_id, args.category, args.title, args.content),
        )
        conn.commit()
        print(f"OK: note [{args.category}] {args.title}")

    elif args.action == "list":
        where = "WHERE session_id=?"
        params = [args.session_id]
        if getattr(args, "category", None):
            where += " AND category=?"; params.append(args.category)
        rows = conn.execute(
            f"SELECT category, title, content FROM architecture_notes {where} ORDER BY category, id",
            params,
        ).fetchall()
        for r in rows:
            content_preview = (r["content"] or "")[:80]
            print(f"[{r['category']}] {r['title']}\n  {content_preview}")

    conn.close()


# ---------------------------------------------------------------------------
# コマンド: context
# ---------------------------------------------------------------------------

def cmd_context(args):
    conn = get_db(args.db)

    if args.action == "summary":
        # セッション情報
        sess = conn.execute("SELECT * FROM analysis_sessions WHERE id=?", (args.session_id,)).fetchone()
        if not sess:
            print(f"ERROR: session {args.session_id} not found")
            return

        lines = [
            "=" * 60,
            f"セッション: {sess['repo_name']} (id={sess['id']})",
            f"  リポジトリ: {sess['repo_path']}",
            f"  ステータス: {sess['status']}",
            f"  言語/FW: {sess['tech_stack'] or '未設定'}",
            f"  種別: {sess['project_type'] or '未設定'}",
            f"  アーキテクチャ: {sess['arch_pattern'] or '未設定'}",
        ]

        # ステップ状態
        steps = conn.execute(
            "SELECT phase, step_name, status, agent_id, summary FROM analysis_steps WHERE session_id=? ORDER BY phase, id",
            (args.session_id,),
        ).fetchall()
        lines.append("\n--- 解析ステップ状態 ---")
        for s in steps:
            icon = {"completed": "✓", "claimed": "→", "pending": "○", "skipped": "-"}.get(s["status"], "?")
            agent = f" [{s['agent_id']}]" if s["agent_id"] else ""
            summary = f" : {s['summary']}" if s["summary"] else ""
            lines.append(f"  {icon} Phase{s['phase']} {s['step_name']}{agent}{summary}")

        # 件数サマリー
        ep_count = conn.execute("SELECT COUNT(*) FROM endpoints WHERE session_id=?", (args.session_id,)).fetchone()[0]
        md_count = conn.execute("SELECT COUNT(*) FROM data_models WHERE session_id=?", (args.session_id,)).fetchone()[0]
        dm_count = conn.execute("SELECT COUNT(*) FROM functional_domains WHERE session_id=?", (args.session_id,)).fetchone()[0]
        fi_count = conn.execute("SELECT COUNT(*) FROM scanned_files WHERE session_id=?", (args.session_id,)).fetchone()[0]
        an_count = conn.execute("SELECT COUNT(*) FROM architecture_notes WHERE session_id=?", (args.session_id,)).fetchone()[0]

        lines.append(f"\n--- 蓄積データ件数 ---")
        lines.append(f"  エンドポイント: {ep_count}件")
        lines.append(f"  データモデル:   {md_count}件")
        lines.append(f"  機能ドメイン:   {dm_count}件")
        lines.append(f"  解析済みファイル: {fi_count}件")
        lines.append(f"  アーキテクチャメモ: {an_count}件")
        lines.append("=" * 60)

        print("\n".join(lines))

    elif args.action == "export":
        # 特定セクションの詳細エクスポート（ドキュメント生成用）
        section = args.section

        if section == "endpoints":
            rows = conn.execute(
                "SELECT method, path, description, auth_required, path_params, query_params, request_body, response_body, response_status, domain_name FROM endpoints WHERE session_id=? ORDER BY domain_name, path",
                (args.session_id,),
            ).fetchall()
            for r in rows:
                auth = "要" if r["auth_required"] else "不要"
                print(f"\n### {r['method']} {r['path']}")
                if r["description"]: print(f"{r['description']}")
                if r["domain_name"]: print(f"ドメイン: {r['domain_name']}")
                print(f"認証: {auth}")
                if r["path_params"]: print(f"パスパラメータ: {r['path_params']}")
                if r["query_params"]: print(f"クエリパラメータ: {r['query_params']}")
                if r["request_body"]: print(f"リクエスト例:\n{r['request_body']}")
                if r["response_body"]: print(f"レスポンス例 ({r['response_status']}):\n{r['response_body']}")

        elif section == "models":
            rows = conn.execute(
                "SELECT model_name, table_name, description, fields, relations, indexes, domain_name FROM data_models WHERE session_id=? ORDER BY domain_name, model_name",
                (args.session_id,),
            ).fetchall()
            for r in rows:
                print(f"\n### {r['model_name']} (テーブル: {r['table_name'] or 'N/A'})")
                if r["description"]: print(r["description"])
                if r["domain_name"]: print(f"ドメイン: {r['domain_name']}")
                if r["fields"]:
                    print("フィールド:")
                    for f in json.loads(r["fields"]):
                        pk = " [PK]" if f.get("pk") else ""
                        nullable = "" if f.get("nullable", True) else " NOT NULL"
                        print(f"  - {f.get('name')}: {f.get('type')}{pk}{nullable}")
                if r["relations"]:
                    print("リレーション:")
                    for rel in json.loads(r["relations"]):
                        print(f"  - {rel.get('type')} {rel.get('target')} ({rel.get('fk', '')})")

        elif section == "domains":
            rows = conn.execute(
                "SELECT domain_name, description, screens, screen_transitions, business_rules FROM functional_domains WHERE session_id=? ORDER BY domain_name",
                (args.session_id,),
            ).fetchall()
            for r in rows:
                print(f"\n### {r['domain_name']}")
                if r["description"]: print(r["description"])
                if r["screens"]:
                    print("画面一覧:")
                    for s in json.loads(r["screens"]):
                        print(f"  - {s.get('name')}: {s.get('description', '')}")
                if r["business_rules"]:
                    print("ビジネスルール:")
                    for rule in json.loads(r["business_rules"]):
                        print(f"  - {rule}")

        elif section == "architecture":
            rows = conn.execute(
                "SELECT category, title, content FROM architecture_notes WHERE session_id=? ORDER BY category, id",
                (args.session_id,),
            ).fetchall()
            for r in rows:
                print(f"\n[{r['category']}] {r['title']}\n{r['content']}")

    conn.close()


# ---------------------------------------------------------------------------
# メインパーサー
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="re_db.py",
        description="リバースエンジニアリング解析用SQLite管理CLI",
    )
    parser.add_argument("--db", default=".re_analysis.db", help="SQLiteDBファイルパス")

    sub = parser.add_subparsers(dest="command", required=True)

    # --- init ---
    p_init = sub.add_parser("init", help="DBを初期化（冪等）")

    # --- session ---
    p_sess = sub.add_parser("session", help="セッション管理")
    p_sess.add_argument("action", choices=["create", "get", "update", "set-meta"])
    p_sess.add_argument("--repo-path", help="リポジトリの絶対パス")
    p_sess.add_argument("--repo-name", help="リポジトリ名")
    p_sess.add_argument("--session-id", type=int, help="セッションID")
    p_sess.add_argument("--status", help="新しいステータス")
    p_sess.add_argument("--tech-stack", help="技術スタック (JSON文字列)")
    p_sess.add_argument("--project-type", help="プロジェクト種別")
    p_sess.add_argument("--arch-pattern", help="アーキテクチャパターン")
    p_sess.add_argument("--entry-points", help="エントリーポイント (JSON配列)")

    # --- step ---
    p_step = sub.add_parser("step", help="解析ステップ管理")
    p_step.add_argument("action", choices=["claim", "done", "skip", "list", "pending"])
    p_step.add_argument("--session-id", type=int, required=True)
    p_step.add_argument("--phase", type=int, help="フェーズ番号 (1/2/3)")
    p_step.add_argument("--step", help="ステップ名")
    p_step.add_argument("--agent-id", help="エージェントID")
    p_step.add_argument("--summary", help="完了時のサマリー")

    # --- file ---
    p_file = sub.add_parser("file", help="解析済みファイルキャッシュ")
    p_file.add_argument("action", choices=["add", "exists", "list"])
    p_file.add_argument("--session-id", type=int, required=True)
    p_file.add_argument("--path", help="ファイルパス")
    p_file.add_argument("--category", help="ファイルカテゴリ")
    p_file.add_argument("--summary", help="ファイル内容のサマリー")
    p_file.add_argument("--key-elements", help="主要要素 (JSON)")
    p_file.add_argument("--agent-id", help="エージェントID")

    # --- endpoint ---
    p_ep = sub.add_parser("endpoint", help="APIエンドポイント管理")
    p_ep.add_argument("action", choices=["add", "list", "set-domain"])
    p_ep.add_argument("--session-id", type=int, required=True)
    p_ep.add_argument("--json", help="エンドポイントデータ (JSON)")
    p_ep.add_argument("--domain", help="ドメイン名でフィルタ / set-domainで指定")
    p_ep.add_argument("--method", help="HTTPメソッド (set-domain用)")
    p_ep.add_argument("--path", help="エンドポイントパス (set-domain用)")

    # --- model ---
    p_model = sub.add_parser("model", help="データモデル管理")
    p_model.add_argument("action", choices=["add", "list"])
    p_model.add_argument("--session-id", type=int, required=True)
    p_model.add_argument("--json", help="モデルデータ (JSON)")

    # --- domain ---
    p_domain = sub.add_parser("domain", help="機能ドメイン管理")
    p_domain.add_argument("action", choices=["add", "update", "list"])
    p_domain.add_argument("--session-id", type=int, required=True)
    p_domain.add_argument("--name", help="ドメイン名")
    p_domain.add_argument("--desc", help="説明")
    p_domain.add_argument("--json", help="詳細データ (JSON)")

    # --- note ---
    p_note = sub.add_parser("note", help="アーキテクチャメモ管理")
    p_note.add_argument("action", choices=["add", "list"])
    p_note.add_argument("--session-id", type=int, required=True)
    p_note.add_argument("--category", help="カテゴリ")
    p_note.add_argument("--title", help="タイトル")
    p_note.add_argument("--content", help="メモ内容")

    # --- context ---
    p_ctx = sub.add_parser("context", help="コンテキスト管理")
    p_ctx.add_argument("action", choices=["summary", "export"])
    p_ctx.add_argument("--session-id", type=int, required=True)
    p_ctx.add_argument("--section", choices=["endpoints", "models", "domains", "architecture"],
                       help="exportするセクション")

    return parser


COMMAND_MAP = {
    "init": cmd_init,
    "session": cmd_session,
    "step": cmd_step,
    "file": cmd_file,
    "endpoint": cmd_endpoint,
    "model": cmd_model,
    "domain": cmd_domain,
    "note": cmd_note,
    "context": cmd_context,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    fn = COMMAND_MAP.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
