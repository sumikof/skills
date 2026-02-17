#!/usr/bin/env python3
"""Windows Python GUIプロジェクトの雛形を生成するスクリプト。

使い方:
    python setup_project.py <project_name> [output_dir] [--skill-dir <skill_base_dir>]

例:
    python setup_project.py MyApp
    python setup_project.py MyApp C:/Projects
    python setup_project.py MyApp . --skill-dir C:/path/to/skill
"""

import argparse
import shutil
import sys
from pathlib import Path


def setup_project(project_name: str, output_dir: Path, template_dir: Path) -> None:
    project_dir = output_dir / project_name

    if project_dir.exists():
        print(f"Error: {project_dir} already exists.")
        sys.exit(1)

    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    # テンプレートをコピー
    shutil.copytree(template_dir, project_dir)

    # {APP_NAME} プレースホルダーを置換
    for path in project_dir.rglob("*"):
        if path.is_file() and path.suffix in (".py", ".spec", ".txt", ".md"):
            try:
                text = path.read_text(encoding="utf-8")
                if "{APP_NAME}" in text:
                    path.write_text(text.replace("{APP_NAME}", project_name), encoding="utf-8")
            except Exception:
                pass  # バイナリファイル等はスキップ

    print(f"✅ プロジェクト '{project_name}' を作成しました: {project_dir}")
    print()
    print("次のステップ:")
    print(f"  1. cd {project_dir}")
    print(f"  2. python -m venv venv")
    print(f"  3. venv\\Scripts\\activate")
    print(f"  4. pip install -r requirements.txt")
    print(f"  5. python main.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows Python GUIプロジェクトを初期化します")
    parser.add_argument("project_name", help="プロジェクト名（ディレクトリ名にもなります）")
    parser.add_argument("output_dir", nargs="?", default=".", help="出力先ディレクトリ（デフォルト: カレント）")
    parser.add_argument("--skill-dir", help="スキルのベースディレクトリ（省略時はスクリプトの2階層上を自動検出）")
    args = parser.parse_args()

    # テンプレートディレクトリを解決
    if args.skill_dir:
        template_dir = Path(args.skill_dir) / "assets" / "template"
    else:
        # このスクリプトは skills/scripts/ にあるので ../assets/template を探す
        template_dir = Path(__file__).parent.parent / "assets" / "template"

    setup_project(
        project_name=args.project_name,
        output_dir=Path(args.output_dir).resolve(),
        template_dir=template_dir,
    )


if __name__ == "__main__":
    main()
