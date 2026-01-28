#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建测试用户和示例数据
"""

from app import app, db, User, Account, Transaction, BankCard, Message
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def init_database():
    """初始化数据库并创建测试数据"""

    with app.app_context():
        # 删除旧数据并重建表
        db.drop_all()
        db.create_all()

        print("正在创建测试用户...")

        # 创建测试用户
        users_data = [
            {
                'username': 'zhangsan',
                'password': '123456',
                'real_name': '张三',
                'id_card': '110101199001011234',
                'phone': '13800138001',
                'email': 'zhangsan@example.com',
                'address': '北京市朝阳区建国路88号'
            },
            {
                'username': 'lisi',
                'password': '123456',
                'real_name': '李四',
                'id_card': '310101199202022345',
                'phone': '13900139002',
                'email': 'lisi@example.com',
                'address': '上海市浦东新区陆家嘴金融中心'
            },
            {
                'username': 'wangwu',
                'password': '123456',
                'real_name': '王五',
                'id_card': '440101199303033456',
                'phone': '13700137003',
                'email': 'wangwu@example.com',
                'address': '广东省深圳市南山区科技园'
            },
            {
                'username': 'zhaoliu',
                'password': '123456',
                'real_name': '赵六',
                'id_card': '330101199404044567',
                'phone': '13600136004',
                'email': 'zhaoliu@example.com',
                'address': '浙江省杭州市西湖区文三路'
            },
            {
                'username': 'sunqi',
                'password': '123456',
                'real_name': '孙七',
                'id_card': '320101199505055678',
                'phone': '13500135005',
                'email': 'sunqi@example.com',
                'address': '江苏省南京市鼓楼区中山路'
            }
        ]

        users = []
        for data in users_data:
            user = User(
                username=data['username'],
                password_hash=generate_password_hash(data['password']),
                real_name=data['real_name'],
                id_card=data['id_card'],
                phone=data['phone'],
                email=data['email'],
                address=data['address']
            )
            db.session.add(user)
            users.append(user)

        db.session.commit()
        print(f"已创建 {len(users)} 个测试用户")

        # 为每个用户创建理财账户
        print("正在创建理财账户...")
        accounts = []
        account_types = ['活期账户', '定期理财', '基金账户']

        for i, user in enumerate(users):
            # 每个用户创建2-3个账户
            num_accounts = random.randint(2, 3)
            for j in range(num_accounts):
                account = Account(
                    account_no=f'YX2024{str(user.id).zfill(4)}{str(j+1).zfill(4)}',
                    user_id=user.id,
                    account_type=account_types[j % len(account_types)],
                    balance=round(random.uniform(10000, 500000), 2),
                    frozen_amount=round(random.uniform(0, 5000), 2)
                )
                db.session.add(account)
                accounts.append(account)

        db.session.commit()
        print(f"已创建 {len(accounts)} 个理财账户")

        # 创建交易记录
        print("正在创建交易记录...")
        trans_types = ['转入', '转出', '收益', '手续费']
        trans_desc = {
            '转入': ['工资入账', '理财收益', '红包收入', '转账收入', '退款'],
            '转出': ['日常消费', '转账支出', '账单支付', '购物支付'],
            '收益': ['活期利息', '理财收益', '基金分红'],
            '手续费': ['转账手续费', '服务费', '管理费']
        }

        transaction_count = 0
        for account in accounts:
            # 每个账户创建5-10笔交易
            num_trans = random.randint(5, 10)
            current_balance = account.balance

            for k in range(num_trans):
                trans_type = random.choice(trans_types)
                if trans_type in ['转出', '手续费']:
                    amount = -round(random.uniform(100, 5000), 2)
                else:
                    amount = round(random.uniform(500, 20000), 2)

                current_balance += amount

                trans = Transaction(
                    account_id=account.id,
                    trans_type=trans_type,
                    amount=amount,
                    balance_after=round(current_balance, 2),
                    description=random.choice(trans_desc[trans_type]),
                    target_account=f'YX{random.randint(100000, 999999)}' if trans_type in ['转入', '转出'] else None,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                db.session.add(trans)
                transaction_count += 1

        db.session.commit()
        print(f"已创建 {transaction_count} 条交易记录")

        # 创建银行卡
        print("正在创建银行卡...")
        banks = [
            ('工商银行', 'card-icbc'),
            ('建设银行', 'card-ccb'),
            ('农业银行', 'card-abc'),
            ('中国银行', 'card-boc'),
            ('招商银行', ''),
            ('交通银行', '')
        ]

        card_count = 0
        for user in users:
            # 每个用户绑定1-2张银行卡
            num_cards = random.randint(1, 2)
            for m in range(num_cards):
                bank = random.choice(banks)
                card = BankCard(
                    user_id=user.id,
                    card_no=f'62{random.randint(10, 99)}{random.randint(1000000000000, 9999999999999)}',
                    bank_name=bank[0],
                    card_type=random.choice(['储蓄卡', '信用卡']),
                    holder_name=user.real_name,
                    bindded_phone=user.phone
                )
                db.session.add(card)
                card_count += 1

        db.session.commit()
        print(f"已创建 {card_count} 张银行卡")

        # 创建站内消息
        print("正在创建站内消息...")
        msg_templates = [
            {
                'title': '欢迎加入云享财富！',
                'content': '尊敬的用户，感谢您注册云享财富平台。我们为您提供安全、便捷的理财服务。请完善个人信息并绑定银行卡，开始您的理财之旅！',
                'msg_type': '系统通知'
            },
            {
                'title': '账户资金变动提醒',
                'content': '您的账户于今日收到一笔转账，金额为 ¥15,000.00，请注意查收。如非本人操作，请立即联系客服。',
                'msg_type': '交易提醒'
            },
            {
                'title': '您的理财产品即将到期',
                'content': '您购买的"稳健增值90天"理财产品将于3天后到期，届时本金和收益将自动转入您的活期账户。',
                'msg_type': '交易提醒'
            },
            {
                'title': '异地登录提醒',
                'content': '您的账户于2024-01-15 14:30:25在新设备上登录，登录地点：上海市。如非本人操作，请立即修改密码。',
                'msg_type': '安全提醒'
            },
            {
                'title': '密码修改成功',
                'content': '您的登录密码已于2024-01-10 09:15:30成功修改。如非本人操作，请立即联系客服。',
                'msg_type': '安全提醒'
            },
            {
                'title': '理财收益到账通知',
                'content': '您的"月月盈"理财产品本期收益 ¥1,258.36 已到账，请查收。继续持有可获得更多收益！',
                'msg_type': '交易提醒'
            },
            {
                'title': '实名认证成功',
                'content': '恭喜您已成功完成实名认证，现在可以使用平台全部功能。祝您理财愉快！',
                'msg_type': '系统通知'
            },
            {
                'title': '大额转账验证码',
                'content': '您正在进行大额转账操作，转账金额 ¥50,000.00，验证码为 836592，有效期5分钟。请勿将验证码告知他人！',
                'msg_type': '安全提醒'
            }
        ]

        msg_count = 0
        for user in users:
            # 每个用户3-5条消息
            num_msgs = random.randint(3, 5)
            selected_msgs = random.sample(msg_templates, min(num_msgs, len(msg_templates)))

            for msg_data in selected_msgs:
                msg = Message(
                    user_id=user.id,
                    title=msg_data['title'],
                    content=msg_data['content'],
                    msg_type=msg_data['msg_type'],
                    is_read=random.choice([True, False]),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 15))
                )
                db.session.add(msg)
                msg_count += 1

        db.session.commit()
        print(f"已创建 {msg_count} 条站内消息")

        print("\n" + "="*50)
        print("数据库初始化完成！")
        print("="*50)
        print("\n测试账号信息：")
        print("-" * 40)
        for data in users_data:
            print(f"用户名: {data['username']:<10} 密码: {data['password']:<10} 姓名: {data['real_name']}")
        print("-" * 40)
        print("\n启动命令: python app.py")
        print("访问地址: http://localhost:5000")


if __name__ == '__main__':
    init_database()
