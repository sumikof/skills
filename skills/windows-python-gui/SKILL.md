---
name: windows-python-gui
description: Windows上で動くPython GUIアプリケーション（tkinter）の開発を支援するスキル。新規プロジェクトの雛形生成、開発環境セットアップ（venv）、tkinterによるGUI実装、PyInstallerによるexeビルド・配布まで一連の流れをサポートする。「Pythonでデスクトップアプリを作りたい」「tkinterでGUIを作りたい」「exeにしたい」「Windowsアプリを配布したい」といった場面で使用する。
---

# Windows Python GUIアプリ開発スキル

## 概要

tkinterを使ったWindows向けPython GUIアプリの開発から配布まで支援する。

## ワークフロー

### 新規プロジェクトを始める

`setup_project.py` スクリプトでプロジェクト雛形を生成する:

```bash
python <skill_base_dir>/scripts/setup_project.py <プロジェクト名> [出力先ディレクトリ]
```

生成されるファイル:
- `main.py` — tkinter App クラスの雛形（高DPI対応済み）
- `app.spec` — PyInstaller specファイル
- `requirements.txt` — 依存パッケージ
- `.gitignore`

### 開発環境セットアップ（Windows PowerShell）

```powershell
# 1. プロジェクトディレクトリへ移動
cd MyApp

# 2. 仮想環境を作成・有効化
python -m venv venv
venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. アプリを起動
python main.py
```

### tkinterでGUIを実装する

`main.py` の `_setup_ui()` メソッドにウィジェットを追加する。

**基本的なレイアウト（pack）:**
```python
def _setup_ui(self):
    frame = ttk.Frame(self, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="名前:").pack(anchor=tk.W)
    entry = ttk.Entry(frame, width=30)
    entry.pack(fill=tk.X)
    ttk.Button(frame, text="実行", command=self._on_submit).pack(pady=5)
```

**グリッドレイアウト（複雑なフォーム向け）:**
```python
def _setup_ui(self):
    frame = ttk.Frame(self, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="名前:").grid(row=0, column=0, sticky=tk.W, padx=5)
    ttk.Entry(frame).grid(row=0, column=1, sticky=tk.EW, padx=5)

    ttk.Label(frame, text="年齢:").grid(row=1, column=0, sticky=tk.W, padx=5)
    ttk.Entry(frame).grid(row=1, column=1, sticky=tk.EW, padx=5)
```

**よく使うウィジェット:**

| 目的 | ウィジェット |
| ---- | ------------ |
| テキスト表示 | `ttk.Label` |
| 1行入力 | `ttk.Entry` |
| 複数行入力 | `tk.Text` |
| ボタン | `ttk.Button` |
| ドロップダウン | `ttk.Combobox` |
| チェックボックス | `ttk.Checkbutton` |
| ラジオボタン | `ttk.Radiobutton` |
| ファイル選択 | `filedialog.askopenfilename()` |
| メッセージ | `messagebox.showinfo/showerror` |
| プログレスバー | `ttk.Progressbar` |
| タブ | `ttk.Notebook` |

### exeビルド

```powershell
# venv内で実行
pyinstaller app.spec
# dist/MyApp.exe が生成される
```

詳細・トラブルシュートは `references/pyinstaller.md` を参照。

## 参照ファイル

- **Windows固有の注意点**（文字コード・パス・DPI・リソースパス）: `references/windows-gotchas.md`
- **PyInstallerの詳細設定とトラブルシュート**: `references/pyinstaller.md`
