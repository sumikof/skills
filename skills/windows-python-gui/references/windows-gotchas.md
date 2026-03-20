# Windows固有の注意事項

## 文字コード

### ファイルの読み書き
Windowsのデフォルトはcp932（Shift-JIS）。常にエンコーディングを明示する。

```python
# 悪い例 - Windowsではcp932で開く
with open("data.txt") as f:
    text = f.read()

# 良い例 - エンコーディングを明示
with open("data.txt", encoding="utf-8") as f:
    text = f.read()
```

### stdout/stderrの文字化け
```python
import sys
import io
# PyInstallerビルド後のコンソール出力対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
```

### tkinterのラベル・テキスト
tkinterは内部でUnicodeを使うため、日本語文字列はそのまま使える。ただしフォントを指定しないと豆腐になることがある。

```python
# Windowsで日本語が確実に表示されるフォント指定
label = ttk.Label(frame, text="日本語テキスト", font=("Yu Gothic UI", 10))
```

---

## パス操作

### パス区切り文字
`\` ではなく `pathlib.Path` を使う。文字列で書く場合は `/` も使える。

```python
from pathlib import Path

# 良い例
config_path = Path("config") / "settings.json"
data_dir = Path.home() / "AppData" / "Local" / "MyApp"

# 悪い例 - Windowsでしか動かない
config_path = "config\\settings.json"
```

### アプリデータの保存先
ユーザーデータはDocumentsやProgram Filesではなく`AppData`に保存する。

```python
from pathlib import Path
import os

# ユーザー設定・データの保存先
app_data = Path(os.environ["APPDATA"]) / "MyApp"      # ローミング
local_data = Path(os.environ["LOCALAPPDATA"]) / "MyApp"  # ローカル
app_data.mkdir(parents=True, exist_ok=True)
```

### exe実行時のカレントディレクトリ
PyInstallerでビルドしたexeではスクリプトのディレクトリが変わる。

```python
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """スクリプト/exeのベースディレクトリを返す"""
    if getattr(sys, "frozen", False):
        # PyInstallerでビルドされたexe
        return Path(sys.executable).parent
    else:
        # 通常のPythonスクリプト
        return Path(__file__).parent
```

---

## DPI・フォント

### 高DPI対応
4K・高解像度ディスプレイでUIが小さくなる問題を防ぐ。

```python
import tkinter as tk
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)  # アプリ起動前に呼ぶ
except Exception:
    pass

root = tk.Tk()
```

### tkinterのデフォルトフォント変更
```python
import tkinter as tk
from tkinter import font

root = tk.Tk()
# アプリ全体のデフォルトフォントを変更
default_font = font.nametofont("TkDefaultFont")
default_font.configure(family="Yu Gothic UI", size=10)
root.option_add("*Font", default_font)
```

---

## exe実行時の一時ディレクトリ

PyInstallerの`--onefile`ビルドではexe起動時に`%TEMP%\_MEIxxxxxx`に展開される。
データファイルのパスは`sys._MEIPASS`で取得する。

```python
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """バンドルされたリソースの絶対パスを返す"""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path
```

---

## よくあるエラー

| エラー | 原因 | 対策 |
| ------ | ---- | ---- |
| `UnicodeDecodeError` | ファイル読み込み時のエンコーディング不一致 | `encoding="utf-8"` を明示 |
| tkinterで豆腐文字 | フォント未指定 | `font=("Yu Gothic UI", 10)` を指定 |
| exeが起動しない（無音で終了） | 例外が握りつぶされている | `console=True`でビルドしてエラー確認 |
| exeでリソースファイルが見つからない | パスが開発時と異なる | `get_resource_path()`を使う |
| ウィンドウが小さすぎる | 高DPI非対応 | `SetProcessDpiAwareness(1)`を追加 |
