# PyInstallerでのexeビルド

## 基本的なビルド手順

```bash
# venv内で実行
pip install pyinstaller

# 1ファイルのexeを生成（GUIアプリ、コンソール非表示）
pyinstaller --onefile --windowed --name MyApp main.py

# specファイルを使う場合（推奨）
pyinstaller app.spec
```

出力先: `dist/MyApp.exe`

---

## specファイルの使い方

### データファイルをバンドルする
画像・設定ファイルなどをexeに含める場合、`datas`に指定する。

```python
# app.spec
a = Analysis(
    ['main.py'],
    datas=[
        ('assets/icons', 'assets/icons'),   # ディレクトリごとバンドル
        ('config/default.json', 'config'),  # 個別ファイル
    ],
    ...
)
```

### 自動検出されないモジュールの追加
```python
a = Analysis(
    ...
    hiddenimports=[
        'PIL._tkinter_finder',  # Pillowを使う場合
        'pkg_resources.py2_compat',
    ],
    ...
)
```

### アイコンの設定
```python
exe = EXE(
    ...
    icon='assets/icon.ico',  # .ico形式が必要（.pngは不可）
    ...
)
```

---

## よくあるトラブルと対策

### exeが起動しない（無音で落ちる）
まず`console=True`でビルドしてエラーメッセージを確認する。

```python
# app.spec - デバッグ時は console=True に変更
exe = EXE(..., console=True, ...)
```

### ModuleNotFoundError
`hiddenimports`に不足モジュールを追加する。

```python
# 動的インポートや条件付きインポートは検出されないことがある
hiddenimports=['missing_module_name'],
```

### ウイルス対策ソフトの誤検知
PyInstallerのexeはウイルス対策ソフトに誤検知されやすい。
- UPXを無効化: `upx=False`
- 別の解決策: [PyInstaller公式のFAQ](https://pyinstaller.org/en/stable/faq.html) を参照

### --onefileビルドが遅い
起動のたびに`%TEMP%`に展開するため遅い。
配布用途でなければ`--onedir`（デフォルト）の方が起動が速い。

```bash
# onedir（フォルダ形式）- 起動が速い
pyinstaller --windowed --name MyApp main.py

# onefile（1ファイル）- 配布しやすいが起動が遅い
pyinstaller --onefile --windowed --name MyApp main.py
```

### リソースファイルが見つからない
exeと同じ場所に置かれているファイルは`sys.executable`基準で参照する。
バンドルしたファイルは`sys._MEIPASS`基準。→ `windows-gotchas.md`の`get_resource_path()`を使う。

---

## ビルドサイズを小さくする

```bash
# 不要なモジュールを除外
pyinstaller --onefile --windowed \
  --exclude-module matplotlib \
  --exclude-module numpy \
  main.py
```

specファイルでも指定可能:
```python
a = Analysis(
    ...
    excludes=['matplotlib', 'numpy', 'scipy'],
    ...
)
```

---

## チェックリスト

- [ ] `venv`内でビルドしているか（システムのPythonでビルドすると余計なパッケージが混入）
- [ ] `console=False`になっているか（GUIアプリ）
- [ ] データファイルを`datas`に追加しているか
- [ ] アイコンは`.ico`形式か
- [ ] 別PCで動作確認したか（Visual C++ Redistributable不要か確認）
