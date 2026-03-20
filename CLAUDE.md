# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

個人用のClaude Codeスキルを作成・管理するリポジトリ。スキルはすべて日本語で記述する。

## スキル作成ワークフロー

新しいスキルの作成には **`skill-creator` スキル**を使用すること。ユーザとのヒアリングを繰り返しながら段階的にスキルを構築する。直接ファイルを書き始めないこと。

### SKILL.md の構造

```yaml
---
name: スキル名
description: "トリガー条件を含む詳細な説明文（英語キーワードも含めて検索性を確保）"
---
# 本体（日本語）
```

- `description` はスキル検索のマッチングに使われるため、ユーザが使いそうな表現・キーワードを網羅的に含める
- 本体には ワークフロー、パターン選択表、コード例、リファレンスへのリンクを記載

## プロジェクト構成

```
skills/
├── CLAUDE.md
├── pyproject.toml          # uv プロジェクト設定
├── .venv/                  # uv 管理の仮想環境
└── skills/                 # スキル格納ディレクトリ
    ├── langgraph-agent/    # LangGraphエージェント構築スキル
    ├── langgraph-neo4j/    # LangGraph + Neo4jグラフDBスキル
    ├── windows-python-gui/ # Windows Python GUIスキル
    └── yfinance-jp-stock/  # yfinanceによる日本株情報取得スキル
```

## Python環境

- `uv` でパッケージ管理。`.venv` はプロジェクトルートに配置
- スクリプト実行時は `.venv` の環境を使用する: `source .venv/bin/activate`

## 注意事項

- `.gitignore` で `*.skill` を除外している
- skill-creatorの最終ステップ（`package_skill.py`による`*.skill`パッケージ化）は不要。実施しないこと
- 許可済みドメイン: langchain-ai.github.io, github.com, pypi.org 等（`.claude/settings.local.json` 参照）
