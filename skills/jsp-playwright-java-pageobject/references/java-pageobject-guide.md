# Java ページオブジェクト生成ガイド(サブエージェント用)

あなたは jsp-playwright-doc が生成した1枚のMarkdownドキュメント(画面概要 / 要素(ロケーター) / オペレーション / 遷移先 の4セクション)から、**Playwright for Java** のページオブジェクトクラスを1つ生成する。以下の規約に厳密に従うこと。

## 0. 入出力

- 入力: 解析済みMarkdown(UTF-8)1枚
- 出力: Javaソースファイル1枚(UTF-8)。呼び出し元から指定された出力パス・パッケージ名・クラス名を**そのまま**使う(自分で命名し直さない)
- 呼び出し元から**クラス対応表**(JSPパス → 完全修飾クラス名)が渡される。遷移先クラスの解決はこの表だけを根拠にする

## 1. クラス構造(この形を厳守)

```java
package pages.user;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.options.AriaRole;
import com.microsoft.playwright.options.SelectOption;

/**
 * ユーザー編集画面 (user/edit.jsp) のページオブジェクト。
 *
 * <p>目的: 既存ユーザーの氏名・権限・性別・有効フラグを編集し、更新する画面。</p>
 * <ul>
 *   <li>URL/マッピング: form action={@code /app/user/update.do} (POST)</li>
 *   <li>include: /common/header.jsp(中身は未解析)</li>
 *   <li>submit 時に hidden {@code id}(対象ユーザーID)が送信される</li>
 * </ul>
 */
public class EditPage {

    private final Page page;

    // ==== 要素(ロケーター) ====

    /** 氏名 (text入力)。候補: [name="name"] / getByLabel("氏名")。Spring form:input からの推定 */
    public final Locator userName;

    /** 権限 (select)。候補: getByLabel("権限")。option は ${roles} から動的生成、選択肢は実行時要確認 */
    public final Locator role;

    /** 有効 (checkbox)。候補: #active。Spring form:checkbox からの推定 */
    public final Locator active;

    /** 更新ボタン (submit)。候補: getByRole(BUTTON, name="更新")。★トリガー: ユーザー更新 */
    public final Locator updateButton;

    /** 一覧へ戻るリンク。候補: a[href="list.jsp"]。★トリガー: 一覧画面へ遷移 */
    public final Locator backToListLink;

    public EditPage(Page page) {
        this.page = page;
        this.userName = page.locator("#userName");
        this.role = page.locator("[name='roleId']");
        this.active = page.locator("[name='active']");
        this.updateButton = page.locator("#updateBtn");
        this.backToListLink = page.getByRole(AriaRole.LINK,
                new Page.GetByRoleOptions().setName("一覧へ戻る"));
    }

    /**
     * 性別ラジオ (name=gender)。value で個別特定する ("M"=男 / "F"=女)。
     *
     * @param value ラジオの value
     */
    public Locator gender(String value) {
        return page.locator("input[name='gender'][value='" + value + "']");
    }

    // ==== オペレーション ====

    /**
     * ユーザー更新。
     *
     * <p>氏名・権限・性別・有効フラグを設定し、「更新」ボタン(トリガー要素)を押下する。</p>
     * <p>遷移先: {@code /app/user/update.do} — 遷移先JSPが不明のためページオブジェクトは返さない。</p>
     *
     * @param name        氏名
     * @param roleValue   権限 option の value(${roles} から動的生成)
     * @param genderValue 性別の value ("M"/"F")
     * @param isActive    有効フラグ
     */
    public void updateUser(String name, String roleValue, String genderValue, boolean isActive) {
        userName.fill(name);
        role.selectOption(roleValue);
        gender(genderValue).check();
        active.setChecked(isActive);
        updateButton.click();
    }

    /**
     * 一覧画面へ遷移。
     *
     * <p>「一覧へ戻る」リンク(トリガー要素)を押下する。遷移先: user/list.jsp</p>
     *
     * @return 遷移先のユーザー一覧画面
     */
    public ListPage backToList() {
        backToListLink.click();
        return new ListPage(page);
    }
}
```

規約のポイント:

- `private final Page page` + コンストラクタで受け取る
- **静的ロケーター = `public final Locator` フィールド**(コンストラクタで初期化)。**動的・パラメータ付きロケーター = 引数付きメソッド**
- フィールドのJavadocに: 論理名(日本語)・種別・**候補ロケーター**・備考(推定/動的の注記)・トリガーなら `★トリガー: <オペレーション名>`
- クラスJavadocに: 画面概要セクションの内容(目的 / URLマッピング / include / hidden等の備考)

## 2. 命名規約(呼び出し元の対応表が正。自分では決めない)

参考として、対応表は次の決定則で作られている:

- パッケージ: `<パッケージルート>.<mdの相対ディレクトリをドット区切り>`(例: `user/edit.md` → `pages.user`)
- クラス名: mdファイル名(拡張子除く)を `_`/`-`/`.` 区切りでPascalCase化し `Page` を付ける(例: `edit.md` → `EditPage`、`user_list.md` → `UserListPage`)
- フィールド名・メソッド名: 論理名/オペレーション名の**意味を表す英語**をlowerCamelCaseで。対応が一目で分かるよう、Javadocの1行目に必ず日本語の論理名/オペレーション名をそのまま書く

| 日本語名の型 | メソッド名パターン | 例 |
|---|---|---|
| <動作>する系(ログイン/検索/更新/登録) | 英語動詞 | `login` / `search` / `updateUser` / `register` |
| <画面>へ遷移 | `goTo<画面>` | 新規登録画面へ遷移 → `goToRegister` |
| <画面>へ戻る | `backTo<画面>` | 一覧へ戻る → `backToList` |
| ボタン/リンク要素 | `<名前>Button` / `<名前>Link` | 更新ボタン → `updateButton` |

## 3. ロケーター記法 → Playwright for Java 変換表

ドキュメントの「推奨ロケーター」を**そのまま採用**する(勝手に別のロケーターへ差し替えない)。候補ロケーターはJavadocに残す。

| ドキュメントの記法 | Java コード |
|---|---|
| `#userId` (id=userId) | `page.locator("#userId")` |
| `name=userId` / `[name="userId"]` | `page.locator("[name='userId']")` |
| `getByRole("button", name="ログイン")` | `page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("ログイン"))` |
| `getByRole("link", name="新規登録")` | `page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("新規登録"))` |
| `getByLabel("ユーザーID")` | `page.getByLabel("ユーザーID")` |
| CSSセレクタ全般 | `page.locator("<そのまま>")` |
| 行スコープで `getByRole("link", name="編集")` | `row.getByRole(AriaRole.LINK, new Locator.GetByRoleOptions().setName("編集"))` |

**Javaで書く際の注意(コンパイルエラーの定番)**:

- role名は `AriaRole` 列挙型(`AriaRole.BUTTON` / `LINK` / `ROW` / `TEXTBOX` / `COMBOBOX` 等)。文字列やJSオブジェクト記法(`{name: ...}`)は**存在しない**
- オプションクラスは呼び出し元の型に合わせる: `Page.GetByRoleOptions` / `Locator.GetByRoleOptions` は**別クラス**
- import: `com.microsoft.playwright.Page`, `com.microsoft.playwright.Locator`, `com.microsoft.playwright.options.AriaRole`, (ラベル選択を使う場合) `com.microsoft.playwright.options.SelectOption`

## 4. 要素種別ごとの操作

| 種別 | フィールド/メソッド | 操作 |
|---|---|---|
| text/password/number等の入力 | final フィールド | `fill(value)` |
| select | final フィールド | `selectOption(value)`。ラベル指定は `selectOption(new SelectOption().setLabel(label))`。備考に選択肢(value=label)があればJavadocへ転記 |
| radioグループ | 引数付きメソッド `xxx(String value)` で value 特定 | `.check()`。備考に値の一覧(M=男 等)があればJavadocへ |
| checkbox | final フィールド | `.setChecked(boolean)` |
| ボタン/リンク | final フィールド | `.click()` |
| **hidden** | **フィールド化しない**。重要パラメータ(csrf/id等)はクラスJavadocに一言残す | — |

## 5. 動的ロケーター・繰り返し行

備考に「動的」「`${...}`」「行スコープ」とある要素は**固定値のロケーターにしない**:

- 行ごとに動的なid(`edit_${u.id}` 等)→ 行を特定する引数付きメソッドにする:

```java
/**
 * ユーザー名で特定した一覧の行。編集リンクの id は edit_${u.id} で動的なため行スコープで取得する。
 *
 * @param userName 行内に表示されるユーザー名
 */
public Locator rowByUserName(String userName) {
    return page.getByRole(AriaRole.ROW, new Page.GetByRoleOptions().setName(userName));
}

/** 編集(行内)リンク。★トリガー: ユーザー編集画面へ遷移 */
public Locator editLinkInRow(String userName) {
    return rowByUserName(userName).getByRole(AriaRole.LINK,
            new Locator.GetByRoleOptions().setName("編集"));
}
```

- オペレーション側も同じ引数を取る(`goToEdit(String userName)`)。行インデックス版の代替(`nth`)を追加してもよい

## 6. オペレーション → メソッド

ドキュメントの**全オペレーションを漏れなく**メソッド化する。各メソッドで:

1. Javadoc 1行目 = **日本語オペレーション名そのまま**(トレーサビリティの要)
2. 手順どおりに実装: 入力要素へ `fill`/`selectOption`/`check` → **トリガー要素**を `click()`
3. 入力要素はメソッド引数にする(入力要素「なし」なら引数なし)
4. 備考(formaction上書き / formnovalidate / 送信値分岐 / hidden送信 等)はJavadocに引き継ぐ
5. 同一フォーム複数遷移先は**ドキュメントのオペレーション分割をそのまま維持**(1メソッドに統合しない)

## 7. 遷移先の返却(全か無かにしない — 1オペレーションずつ判定)

各オペレーションの返り値を、遷移先表の「遷移先JSP」列と**クラス対応表**から個別に決める:

1. 遷移先JSP列の値から `(推定)` `※内部` クエリ(`?id=...`)を除いてJSPパスを得る
2. 対応表を引く: まず**そのままのパス**で、無ければ**現在のmdのディレクトリ基準の相対パス**で解決(例: `user/edit.md` 内の `list.jsp` → `user/list.jsp`)
3. ヒット → そのクラスを返す: `トリガー.click(); return new ListPage(page);`(必要なら import)。`(推定)` 付きならJavadocに「遷移先は推定」と残す
4. ヒットしない / 「不明」/ 対象外 → `void` + Javadocに理由(「遷移先JSP不明のためページオブジェクトは返さない」「register.jsp はドキュメント対象外」等)

**一部の遷移先が不明でも、解決できるものは必ず返す。** 全メソッドを void にするのは誤り。

## 8. 自己検証(出力後、不備は直してから完了)

- ドキュメントの全オペレーションがメソッド化されているか(数を突き合わせる)
- 推奨ロケーターがそのまま使われ、候補・備考がJavadocに残っているか
- JSスタイルAPI(`getByRole("button", {name})`)や存在しないAPIが混入していないか。`Page.GetByRoleOptions` / `Locator.GetByRoleOptions` の取り違えがないか
- import が使用クラスと過不足なく一致するか(遷移先クラス・SelectOption 含む)
- hidden・外部リンクをフィールド化していないか
- 対応表でヒットする遷移先がすべてページオブジェクト返却になっているか
- 文字化けがないか(出力はUTF-8)
