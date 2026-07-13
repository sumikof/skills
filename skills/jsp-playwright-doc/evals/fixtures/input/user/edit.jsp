<%@ page contentType="text/html; charset=Windows-31J" %>
<%@ taglib prefix="form" uri="http://www.springframework.org/tags/form" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ include file="/common/header.jsp" %>
<html><body>
<h1>ユーザー編集</h1>
<form:form action="/app/user/update.do" method="post" modelAttribute="user">
  <form:hidden path="id" />
  <label>氏名</label><form:input path="name" id="userName" />
  <label>権限</label>
  <form:select path="roleId">
    <form:options items="${roles}" itemValue="id" itemLabel="label" />
  </form:select>
  性別:
  <form:radiobutton path="gender" value="M" />男
  <form:radiobutton path="gender" value="F" />女
  <form:checkbox path="active" />有効
  <input type="submit" value="更新" id="updateBtn" />
</form:form>
<a href="list.jsp">一覧へ戻る</a>
</body></html>
