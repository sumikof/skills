# Slide Patterns (HTML) — 定番パターンのマークアップ集

シンクタンク調査報告書に頻出する11パターンのHTMLスケルトン。クラスは
`designs/thinktank.css` のデザイン契約・部品に対応する。

**スニペット内の文言(「令和8年度○○委託事業」「既存資料整理」等)はすべてダミー。**
構造だけを流用し、文言は必ず入力由来のものに置き換える。入力に対応する文言が
ない要素(副題、タスク説明文など)は言い換えで水増しせず、その要素ごと省略する。

## 共通スケルトン (3層構造)

全スライドの基本形。メッセージ(結論1〜2行)は主張のあるスライドのみ。
スケジュール・一覧表など事実提示のみのスライドでは `.message` を省略する。

```html
<section class="slide">
  <header class="slide-header">
    <div class="chapter">2. 分析結果</div>
    <h1 class="slide-title">DX着手状況の分析結果</h1>
  </header>
  <p class="message">対象企業のDX着手率は<strong>34%</strong>に留まり、主因は人材不足である</p>
  <div class="slide-body">
    <!-- 表・図・テキスト -->
  </div>
  <footer class="footer"><span class="source">出所: ○○調査(2026)より作成</span></footer>
</section>
```

強調は `<strong>`(青太字)。最重要箇所のみ `class="red-frame"` で囲む(赤文字・赤塗りは禁止)。
赤枠は資料全体で0〜2箇所が目安。使うか迷う場合は使わない(赤枠ゼロでよい)。

章扉(`.section-break`)は複数章立てでおおむね10枚を超える資料のみに使う。
それ以下では `.chapter` 表記だけで章を示す。

## 1. 表紙

```html
<section class="slide cover no-num">
  <div class="doc-title">地域中小企業のDX推進実態調査<br>報告書</div>
  <div class="doc-subtitle">— 令和8年度 ○○委託事業 —</div>
  <div class="doc-meta">経済産業省 御中<br>○○総合研究所<br>2026年7月</div>
</section>
```

## 2. 目的・背景 (タイトル+ボディ型、メッセージなし)

```html
<div class="slide-body">
  <div class="box">
    <div class="box-title">背景</div>
    <p>中小企業のDX推進は補助金施策にもかかわらず<strong>停滞</strong>している。…</p>
  </div>
  <div class="box">
    <div class="box-title">目的</div>
    <p>停滞要因の構造把握と施策立案を行う。…</p>
  </div>
</div>
```

仕様書抜粋は `.quote-box` +出典明記。段階フローを添える場合は `.flow` で矢羽を横に並べる。

## 3. 調査内容・タスク分解

ナンバーボールの番号は後続のスケジュール・課題・施策スライドと対応付けて再利用する。

```html
<div class="item">
  <span class="num-ball">1</span>
  <div>
    <div class="item-head">文献調査</div>
    <p>既存統計・先行研究から<strong>DX推進の阻害要因仮説</strong>を整理する。</p>
  </div>
</div>
<!-- タスク数ぶん繰り返し (3〜5個が収まりがよい) -->
```

## 4. 矢羽スケジュール (ガントチャート)

`--cols` に期間の列数を指定。矢羽は `left`/`width` を%で配置(1列=100/cols %)。
節目(MTG・報告等)は `.milestone` 縦線+ラベル。`left` は `calc(ラベル列px + 残り%)`。

```html
<div class="slide-body" style="padding-top:24px">
  <div class="milestone" style="left:calc(190px + (100% - 190px)*0.5)"></div>
  <div class="milestone-label" style="left:calc(190px + (100% - 190px)*0.5);top:0">▼中間報告</div>
  <div class="gantt" style="--cols:6;grid-template-columns:190px repeat(6,1fr);margin-top:20px">
    <div class="gt"></div>
    <div class="gh">4月</div><div class="gh">5月</div><div class="gh">6月</div>
    <div class="gh">7月</div><div class="gh">8月</div><div class="gh">9月</div>
    <div class="gt"><span class="num-ball">1</span>文献調査</div>
    <div class="glane" style="grid-column:2/8">
      <div class="chevron" style="left:1%;width:15%">既存資料整理</div>
    </div>
    <div class="gt"><span class="num-ball">2</span>アンケート調査</div>
    <div class="glane" style="grid-column:2/8">
      <div class="chevron sub" style="left:17.7%;width:31%">設計・実査・集計</div>
    </div>
    <!-- 行を繰り返し -->
  </div>
</div>
```

milestone はボディ直下(gantt の外)に置き、ボディ全高を貫通させる。
右端(100%)付近の節目はラベルがはみ出すため `transform:translateX(-100%)` を
インラインで上書きして内側に収める(このとき「最終報告▼」のように▼を線側に置く)。
矢羽内のテキストは入力にサブ工程があればそれを、なければタスク名を再掲する
(空の矢羽にしない。構造上の再掲は創作にあたらない)。

## 5. 論点整理

パターン3と同じ `.item` 構成で、説明文の代わりに論点(問い)の箇条書きを置く。
1項目3〜4論点まで。キーワードは `<strong>`。

## 6. スコープ定義 (階層分類)

対象= `.m-item.on`(青塗り)、対象外= `.m-item.off`(灰)。左に大分類、右へ展開。

```html
<div class="cols">
  <div class="col box"><div class="box-title">大分類</div>…</div>
  <div class="col">
    <span class="m-item on">対象A</span>
    <span class="m-item on">対象B</span>
    <span class="m-item off">対象外C</span>
  </div>
</div>
<div class="legend"><span class="sw" style="background:#2E75B6"></span>対象
  <span class="sw" style="background:#EDEDED"></span>対象外</div>
```

## 7. 分析結果サマリー (評価表)

メッセージ1行+大きな表。評価は記号(◎○△×)+セル濃淡の二重符号化。

```html
<table class="tt">
  <tr><th>対象</th><th class="c">評価項目1</th><th class="c">評価項目2</th></tr>
  <tr><td>製造業</td><td class="c fill-3">◎</td><td class="c fill-4">△</td></tr>
</table>
```

## 8. 分析詳細 (テキスト表)

「対象者属性 | 発言要旨」等の2〜3列表(`table.tt.striped`)。重要ファインディングスを
`<strong>` にして流し読みでも要点が拾えるようにする。1枚に収まらなければ同レイアウトで
分割しタイトルに (1/2) を付ける。

定量データは横棒グラフ:

```html
<div class="bar-row">
  <div class="bar-label">人材不足</div>
  <div class="bar-track"><div class="bar main" style="width:62%"></div></div>
  <div class="bar-val">62%</div>
</div>
<p class="note">n=1,200、複数回答</p>
```

主系列 `.bar`(青)、最重要1本のみ `.bar.main`(紺)、比較対象 `.bar.ref`(灰)。
円グラフ・ドーナツグラフ・多色グラフは使わない。

## 9. 2軸マトリックス

```html
<div class="matrix" style="grid-template-columns:110px repeat(3,1fr)">
  <div></div><div class="axis">区分A</div><div class="axis">区分B</div><div class="axis">区分C</div>
  <div class="axis">層1</div><div class="m-cell"><span class="m-item">要素</span></div>
  <div class="m-cell"></div><div class="m-cell red-frame"><span class="m-item on">重点</span></div>
  <!-- 行を繰り返し -->
</div>
```

## 10. 課題整理

パターン3と同じ `.item` +ナンバーボール。課題は3〜6件(多い場合はグルーピングを
提案する。勝手に削らない)。**このボール番号を次の施策スライドで同じ形・色で再掲**し、
課題→施策の対応を示すのが最大のポイント。

## 11. 課題・施策対応表 / 考察

対応表型: メッセージなしで3列表をメインに。課題列に前ページのナンバーボールを再掲。

```html
<table class="tt">
  <tr><th style="width:220px">課題</th><th>課題の概要</th><th>解決に向けたアイデア(案)</th></tr>
  <tr><td><span class="num-ball">1</span><strong>IT人材の絶対的不足</strong></td>
      <td>…</td><td>…</td></tr>
</table>
```

考察型: 概念図(`.box`/`.flow`/`.matrix` の組合せ)を先に見せてからテキスト詳述、
またはテキストで書き下し下に補助図。構造化しにくい論点は無理に図解せずテキストで見せる。

## パターン選択の早見表

| 入力が伝えること | パターン |
|---|---|
| なぜやるのか | 2. 目的・背景 |
| 何をやるのか | 3. タスク分解 / 5. 論点整理 |
| いつやるのか | 4. 矢羽スケジュール |
| どこまでやるのか | 6. スコープ定義 |
| 何が分かったか(一望/詳細) | 7. サマリー / 8. 分析詳細 |
| どう分布しているか | 9. 2軸マトリックス |
| 何が問題か / どうすべきか | 10. 課題整理 / 11. 対応表・考察 |

## 収まりの目安 (1280x720)

- ボディの実質高さ約 520px。表なら約12行、`.item` なら4〜5個が上限
- はみ出す場合はスライドを分割する。フォントを縮めて詰め込まない
- テキストだけのスライドを3枚以上連続させない(図解スライドを挟む)
