---
name: jsp-playwright-java-pageobject
description: "jsp-playwright-doc が ./output に生成した画面解析ドキュメント(Markdown)をもとに、Playwright for Java のページオブジェクト(1画面1クラス)のJavaソースコードを生成するスキル。Use when: (1) jsp-playwright-doc の出力ドキュメントからJavaのページオブジェクトを実装したい, (2) JSP解析済みMarkdownをJava+Playwrightのコードに落としたい, (3) E2EテストのページオブジェクトをJavaで自動生成したい。ユーザーが「outputのドキュメントからJavaのページオブジェクトを作って」「PlaywrightのページオブジェクトをJavaで生成して」「ドキュメントをJavaコードにして」等と言ったときに使用する。Keywords: Java, Playwright, Playwright for Java, page object, POM, ページオブジェクト, コード生成, jsp-playwright-doc, output, locator, ロケーター, E2E, chainable"
---

# jsp-playwright-doc ドキュメント → Java Playwright ページオブジェクト生成

`./output` ディレクトリ(jsp-playwright-doc の成果物)配下の各Markdownドキュメントを1画面として、Playwright for Java のページオブジェクト(1画面=1クラス)のJavaソースを生成する。

## 概要

入力ドキュメントは4セクション(画面概要 / 要素(ロケーター) / オペレーション / 遷移先)を持つ。これを次の対応でJavaクラスに変換する。

| ドキュメント | Javaクラス |
|---|---|
| 1ファイル(1画面) | 1クラス(`XxxPage`) |
| 画面概要 | クラスJavadoc |
| 要素(ロケーター)の各行 | `public final Locator` フィールド(動的な要素は引数付きメソッド)+ 候補・備考はJavadoc |
| オペレーション | public メソッド(入力要素=引数、トリガー要素をclick) |
| 遷移先(クラス対応表で解決できるもの) | メソッドの返り値 = 遷移先ページオブジェクト(chainable) |

出力は既定で `./javaoutput` 配下に、パッケージルート `pages` としてドキュメントと同じ階層構成で配置する(例: `output/user/edit.md` → `javaoutput/pages/user/EditPage.java`)。出力先・パッケージルートはユーザー指定があればそれに従う。

## ワークフロー

途中でユーザーに逐一確認する必要はない。入力ディレクトリが不明な場合のみ確認する。

### Phase 1: クラス対応表の確定(最重要)

1. 入力ディレクトリ(既定 `./output`)配下の `*.md` を再帰的に列挙する。0件なら終了。
2. **決定則**で全ファイルの出力先を先に確定する:
   - パッケージ: `<パッケージルート>.<相対ディレクトリのドット区切り>`(例: `user/edit.md` → `pages.user`)
   - クラス名: ファイル名(拡張子除く)を `_`/`-`/`.` 区切りでPascalCase化 + `Page`(例: `edit.md` → `EditPage`)
3. **クラス対応表**を作る。各行: `JSPパス(mdの相対パスの拡張子を.jspに) → 完全修飾クラス名 → 出力Javaパス`。この表が全サブエージェント共通の正となる(各自の思いつき命名を許すと相互参照が壊れる)。

### Phase 2: 1ドキュメント=1サブエージェントで生成(並列)

各Markdownに対して1つずつサブエージェントを起動する(独立作業なので同一ターンで複数起動して並列化してよい。大量の場合は10前後ずつバッチ実行する)。

**必ず専用エージェント `jsp-playwright-java-pageobject-generator` を使う**(Agentツールの `subagent_type`、Workflowなら `agentType` に指定)。使えない場合のみ汎用エージェントにフォールバックし、その際は `references/java-pageobject-guide.md` を必ず読ませること。

サブエージェントへ渡す情報:

```
このタスクを実行してください。
- 入力ドキュメント(絶対パス): <output>/xxx/yyy.md
- 出力Javaファイル(絶対パス): <javaoutput>/pages/xxx/YyyPage.java
- パッケージ名: pages.xxx / クラス名: YyyPage(この名前を厳守)
- クラス対応表(遷移先解決用):
    login.jsp → pages.LoginPage
    user/edit.jsp → pages.user.EditPage
    user/list.jsp → pages.user.ListPage
    ...(全行)
- 生成ガイド: <skill>/references/java-pageobject-guide.md を必ず読んで規約を厳守すること
- 完了したら、出力パスと「フィールド数・メソッド数・ページオブジェクトを返せた/返せなかった遷移」を数行で報告すること
```

返り値には要約だけを求め、Javaソース本文は求めない(コンテキスト節約)。

### Phase 3: 集約と整合検証

1. 対応表の全行に対応するJavaファイルが生成されているか確認する。
2. 参照整合をチェックする: 生成された全ファイルの `import`・`new XxxPage(` が対応表のクラス名と一致するか(grep で突き合わせ)。不一致・未生成があればそのファイルだけ再実行する。
3. `javac` が使える環境ならコンパイル確認する(Playwrightのjarが無い場合はスキップし、その旨を報告に含める)。
4. ユーザーへ「生成クラス数・クラス対応表・void のまま残った遷移(理由付き)・注意点」を簡潔に報告する。

## 重要な規約(詳細は references/java-pageobject-guide.md)

- **推奨ロケーターをそのまま採用**。候補ロケーター・備考(taglib推定・動的注記)はJavadocへ引き継ぐ
- **遷移先の返却は1オペレーションずつ判定**。対応表で解決できる遷移は遷移先クラスを返し、不明のものだけ void + 理由をJavadocに書く。「不明が多いから全部void」は禁止
- 動的ロケーター(`edit_${u.id}` 等)は引数付きメソッドにする。固定値にしない
- hidden はフィールド化しない(重要パラメータはクラスJavadocに一言)
- Javadoc 1行目に日本語の論理名/オペレーション名をそのまま書く(ドキュメントとのトレーサビリティ)
- 出力はUTF-8

## よくある失敗

| 失敗 | 対策 |
|---|---|
| 全遷移メソッドを void にする | 対応表で解決できる遷移は必ずページオブジェクトを返す。判定は1オペレーションずつ |
| サブエージェントが独自にクラス名を決めて参照が壊れる | Phase 1 の対応表を全員に配り、指定名を厳守させる |
| JSスタイルAPI(`getByRole("button", {name})`)の混入 | `AriaRole` 列挙型 + `Page.GetByRoleOptions`/`Locator.GetByRoleOptions`(ガイドの変換表参照) |
| 推奨ロケーターを勝手に差し替える | ドキュメントの推奨列をそのまま使い、候補はJavadocに残す |
| 動的idを固定ロケーター化 | 引数付きメソッド+行スコープ取得に変換 |
| hidden・外部リンクをフィールド化 | 対象外。備考としてJavadocに残すのみ |
| 相対パスの遷移先を解決し損ねる | 対応表をそのままのパス→現mdディレクトリ基準の順で引く |
