<%@ page contentType="text/html; charset=Windows-31J" %>
<%@ include file="/common/header.jsp" %>
<html><body>
<h1>ログイン画面</h1>
<img src="/img/logo.png" alt="ロゴ">
<form action="/app/login.do" method="post">
  <label for="userId">ユーザーID</label>
  <input type="text" id="userId" name="userId" />
  <label for="password">パスワード</label>
  <input type="password" id="password" name="password" />
  <input type="hidden" name="csrf" value="<%= token %>" />
  <button type="submit" id="loginBtn">ログイン</button>
</form>
<a href="register.jsp">新規登録</a>
<a href="https://help.example.com/manual">オンラインマニュアル(外部)</a>
<%@ include file="/common/footer.jsp" %>
</body></html>
