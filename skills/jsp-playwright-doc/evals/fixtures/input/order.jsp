<%@ page contentType="text/html; charset=Windows-31J" %>
<%@ include file="/common/header.jsp" %>
<html><body>
<h1>注文入力画面</h1>
<form action="/app/order/confirm.do" method="post">
  <label for="itemName">商品名</label>
  <input type="text" id="itemName" name="itemName" />
  <label for="qty">数量</label>
  <input type="number" id="qty" name="qty" />
  <!-- 同一フォームだが押すボタンで遷移先が分岐する -->
  <button type="submit" id="confirmBtn">確認画面へ</button>
  <button type="submit" id="draftBtn" formaction="/app/order/saveDraft.do">下書き保存</button>
  <button type="submit" id="cancelBtn" formaction="/app/order/list.do" formnovalidate>キャンセル</button>
</form>
<a href="/app/menu.jsp">メニューへ戻る</a>
</body></html>
