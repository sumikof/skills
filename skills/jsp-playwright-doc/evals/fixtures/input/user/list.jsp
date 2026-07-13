<%@ page contentType="text/html; charset=Windows-31J" %>
<%@ include file="/common/header.jsp" %>
<html><body>
<h1>ユーザー一覧</h1>
<form action="/app/user/search.do" method="get">
  <input type="text" id="keyword" name="keyword" />
  <select id="status" name="status">
    <option value="1">有効</option>
    <option value="0">無効</option>
  </select>
  <button type="submit">検索</button>
</form>
<table>
  <c:forEach var="u" items="${users}">
  <tr>
    <td>${u.name}</td>
    <td><a href="edit.jsp?id=${u.id}" id="edit_${u.id}">編集</a></td>
  </tr>
  </c:forEach>
</table>
<a href="/app/menu.jsp">メニューへ戻る</a>
</body></html>
