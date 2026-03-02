#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云享财富 - 个人理财平台
水平越权漏洞演示靶机

警告：本系统仅用于安全教育和授权渗透测试，请勿用于非法用途
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import os
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yxcf-secret-key-2024-do-not-use-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yuanxiang_finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问该页面'


# ==================== 数据库模型 ====================

class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), nullable=False)  # 身份证号
    phone = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    accounts = db.relationship('Account', backref='user', lazy=True)
    cards = db.relationship('BankCard', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)


class Account(db.Model):
    """理财账户表"""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    account_no = db.Column(db.String(20), unique=True, nullable=False)  # 账户编号
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # 活期、定期、基金
    balance = db.Column(db.Float, default=0.0)
    frozen_amount = db.Column(db.Float, default=0.0)  # 冻结金额
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    transactions = db.relationship('Transaction', backref='account', lazy=True)


class Transaction(db.Model):
    """交易记录表"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    trans_type = db.Column(db.String(20), nullable=False)  # 转入、转出、收益、手续费
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)  # 交易后余额
    description = db.Column(db.String(200))
    target_account = db.Column(db.String(50))  # 对方账户
    created_at = db.Column(db.DateTime, default=datetime.now)


class BankCard(db.Model):
    """银行卡绑定表"""
    __tablename__ = 'bank_cards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_no = db.Column(db.String(19), nullable=False)  # 银行卡号
    bank_name = db.Column(db.String(50), nullable=False)
    card_type = db.Column(db.String(20), nullable=False)  # 储蓄卡、信用卡
    holder_name = db.Column(db.String(50), nullable=False)  # 持卡人姓名
    bindded_phone = db.Column(db.String(11), nullable=False)  # 绑定手机
    created_at = db.Column(db.DateTime, default=datetime.now)


class Message(db.Model):
    """站内消息表"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    msg_type = db.Column(db.String(20), nullable=False)  # 系统通知、交易提醒、安全提醒
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('登录成功，欢迎回来！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')
        id_card = request.form.get('id_card')
        phone = request.form.get('phone')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            real_name=real_name,
            id_card=id_card,
            phone=phone
        )
        db.session.add(user)
        db.session.commit()

        # 自动创建一个活期账户
        account = Account(
            account_no=f'YX{datetime.now().strftime("%Y%m%d")}{random.randint(10000, 99999)}',
            user_id=user.id,
            account_type='活期账户',
            balance=0.0
        )
        db.session.add(account)

        # 发送欢迎消息
        msg = Message(
            user_id=user.id,
            title='欢迎加入云享财富！',
            content='尊敬的用户，感谢您注册云享财富平台。我们为您提供安全、便捷的理财服务。请完善个人信息并绑定银行卡，开始您的理财之旅！',
            msg_type='系统通知'
        )
        db.session.add(msg)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """用户仪表盘"""
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_balance = sum(acc.balance for acc in accounts)
    unread_msgs = Message.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('dashboard.html', accounts=accounts, total_balance=total_balance, unread_msgs=unread_msgs)


@app.route('/profile')
@login_required
def profile():
    """个人信息页面"""
    return render_template('profile.html', user=current_user)


@app.route('/accounts')
@login_required
def accounts():
    """账户列表页面"""
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts.html', accounts=user_accounts)


@app.route('/account/<int:account_id>')
@login_required
def account_detail(account_id):
    """账户详情页面"""
    return render_template('account_detail.html', account_id=account_id)


@app.route('/cards')
@login_required
def cards():
    """银行卡管理页面"""
    user_cards = BankCard.query.filter_by(user_id=current_user.id).all()
    return render_template('cards.html', cards=user_cards)


@app.route('/messages')
@login_required
def messages():
    """消息中心页面"""
    user_messages = Message.query.filter_by(user_id=current_user.id)\
                    .order_by(Message.created_at.desc()).all()
    return render_template('messages.html', messages=user_messages)


# ==================== API接口（包含水平越权漏洞） ====================

@app.route('/api/user/search', methods=['GET'])
@login_required
def api_user_search():
    """
    【漏洞点8】用户搜索接口（SQL注入）
    漏洞：使用字符串拼接构造SQL，未做参数化查询
    攻击者可通过keyword参数注入任意SQL片段
    """
    keyword = request.args.get('keyword', '')

    # 【漏洞】直接拼接SQL语句
    raw_sql = f"""
        SELECT id, username, real_name, phone
        FROM users
        WHERE username LIKE '%{keyword}%'
           OR real_name LIKE '%{keyword}%'
        ORDER BY id DESC
        LIMIT 20
    """
    result = db.session.execute(text(raw_sql))

    return jsonify({
        'code': 200,
        'data': [{
            'id': row.id,
            'username': row.username,
            'real_name': row.real_name,
            'phone': row.phone
        } for row in result]
    })


@app.route('/echo', methods=['GET'])
def echo():
    """
    【漏洞点9】反射型XSS
    漏洞：直接输出用户输入内容，未做任何过滤
    """
    content = request.args.get('content', '')
    return f"<h2>系统回显：</h2>{content}"

@app.route('/api/profile', methods=['GET'])
@login_required
def api_get_profile():
    """
    【漏洞点1】获取用户个人信息
    漏洞：未验证user_id是否属于当前登录用户
    正常请求应该只返回当前用户信息，但这里可以通过修改user_id查看任意用户信息
    """
    # 从请求参数获取user_id，如果没有则使用当前用户ID
    user_id = request.args.get('user_id', current_user.id, type=int)

    # 【漏洞】直接查询，未验证user_id是否为当前用户
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    return jsonify({
        'code': 200,
        'data': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'id_card': user.id_card,  # 敏感信息：身份证号
            'phone': user.phone,       # 敏感信息：手机号
            'email': user.email,
            'address': user.address,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@app.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    """
    【漏洞点2】更新用户个人信息
    漏洞：未验证user_id是否属于当前登录用户，可以修改他人信息
    """
    data = request.get_json()
    user_id = data.get('user_id', current_user.id)

    # 【漏洞】直接更新，未验证user_id是否为当前用户
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'}), 404

    if 'email' in data:
        user.email = data['email']
    if 'address' in data:
        user.address = data['address']
    if 'phone' in data:
        user.phone = data['phone']

    db.session.commit()

    return jsonify({'code': 200, 'msg': '更新成功'})


@app.route('/api/account/<int:account_id>', methods=['GET'])
@login_required
def api_get_account(account_id):
    """
    【漏洞点3】获取账户详情
    漏洞：未验证账户是否属于当前登录用户
    攻击者可以通过遍历account_id查看所有用户的账户余额和交易记录
    """
    # 【漏洞】直接通过ID查询，未验证账户所属用户
    account = Account.query.get(account_id)

    if not account:
        return jsonify({'code': 404, 'msg': '账户不存在'}), 404

    # 获取最近交易记录
    transactions = Transaction.query.filter_by(account_id=account_id)\
                    .order_by(Transaction.created_at.desc()).limit(20).all()

    return jsonify({
        'code': 200,
        'data': {
            'id': account.id,
            'account_no': account.account_no,
            'account_type': account.account_type,
            'balance': account.balance,          # 敏感信息：余额
            'frozen_amount': account.frozen_amount,
            'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'transactions': [{
                'id': t.id,
                'trans_type': t.trans_type,
                'amount': t.amount,
                'balance_after': t.balance_after,
                'description': t.description,
                'target_account': t.target_account,
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for t in transactions]
        }
    })


@app.route('/api/card/<int:card_id>', methods=['GET'])
@login_required
def api_get_card(card_id):
    """
    【漏洞点4】获取银行卡详情
    漏洞：未验证银行卡是否属于当前登录用户
    攻击者可以查看他人绑定的银行卡信息
    """
    # 【漏洞】直接通过ID查询，未验证银行卡所属用户
    card = BankCard.query.get(card_id)

    if not card:
        return jsonify({'code': 404, 'msg': '银行卡不存在'}), 404

    return jsonify({
        'code': 200,
        'data': {
            'id': card.id,
            'card_no': card.card_no,              # 敏感信息：银行卡号
            'bank_name': card.bank_name,
            'card_type': card.card_type,
            'holder_name': card.holder_name,       # 敏感信息：持卡人姓名
            'bindded_phone': card.bindded_phone,   # 敏感信息：绑定手机
            'created_at': card.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@app.route('/api/cards', methods=['GET'])
@login_required
def api_get_cards():
    """获取当前用户的银行卡列表（安全接口）"""
    cards = BankCard.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': card.id,
            'card_no': card.card_no[-4:].rjust(len(card.card_no), '*'),  # 脱敏
            'bank_name': card.bank_name,
            'card_type': card.card_type,
            'holder_name': card.holder_name,
            'created_at': card.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for card in cards]
    })


@app.route('/api/message/<int:message_id>', methods=['GET'])
@login_required
def api_get_message(message_id):
    """
    【漏洞点5】获取消息详情
    漏洞：未验证消息是否属于当前登录用户
    攻击者可以查看他人的站内消息，可能包含敏感的交易提醒等信息
    """
    # 【漏洞】直接通过ID查询，未验证消息所属用户
    msg = Message.query.get(message_id)

    if not msg:
        return jsonify({'code': 404, 'msg': '消息不存在'}), 404

    # 标记为已读
    msg.is_read = True
    db.session.commit()

    return jsonify({
        'code': 200,
        'data': {
            'id': msg.id,
            'title': msg.title,
            'content': msg.content,           # 可能包含敏感信息
            'msg_type': msg.msg_type,
            'is_read': msg.is_read,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@app.route('/api/message/<int:message_id>', methods=['DELETE'])
@login_required
def api_delete_message(message_id):
    """
    【漏洞点6】删除消息
    漏洞：未验证消息是否属于当前登录用户
    攻击者可以删除他人的消息
    """
    # 【漏洞】直接通过ID查询并删除，未验证消息所属用户
    msg = Message.query.get(message_id)

    if not msg:
        return jsonify({'code': 404, 'msg': '消息不存在'}), 404

    db.session.delete(msg)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '删除成功'})


@app.route('/api/messages', methods=['GET'])
@login_required
def api_get_messages():
    """获取当前用户的消息列表（安全接口）"""
    messages = Message.query.filter_by(user_id=current_user.id)\
                .order_by(Message.created_at.desc()).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': msg.id,
            'title': msg.title,
            'msg_type': msg.msg_type,
            'is_read': msg.is_read,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages]
    })


@app.route('/api/transfer', methods=['POST'])
@login_required
def api_transfer():
    """
    【漏洞点7】转账接口
    漏洞：未验证转出账户是否属于当前登录用户
    攻击者可以从他人账户转账到自己账户
    """
    data = request.get_json()
    from_account_id = data.get('from_account_id')
    to_account_no = data.get('to_account_no')
    amount = data.get('amount', 0)

    # 【漏洞】未验证转出账户所属用户
    from_account = Account.query.get(from_account_id)
    to_account = Account.query.filter_by(account_no=to_account_no).first()

    if not from_account:
        return jsonify({'code': 404, 'msg': '转出账户不存在'}), 404

    if not to_account:
        return jsonify({'code': 404, 'msg': '收款账户不存在'}), 404

    if from_account.balance < amount:
        return jsonify({'code': 400, 'msg': '余额不足'}), 400

    if amount <= 0:
        return jsonify({'code': 400, 'msg': '转账金额必须大于0'}), 400

    # 执行转账
    from_account.balance -= amount
    to_account.balance += amount

    # 记录交易
    trans_out = Transaction(
        account_id=from_account.id,
        trans_type='转出',
        amount=-amount,
        balance_after=from_account.balance,
        description=f'转账至{to_account_no}',
        target_account=to_account_no
    )
    trans_in = Transaction(
        account_id=to_account.id,
        trans_type='转入',
        amount=amount,
        balance_after=to_account.balance,
        description=f'来自{from_account.account_no}的转账',
        target_account=from_account.account_no
    )

    db.session.add(trans_out)
    db.session.add(trans_in)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '转账成功'})


# ==================== 安全修复版本的API（供对比学习） ====================

@app.route('/api/secure/profile', methods=['GET'])
@login_required
def api_secure_get_profile():
    """【安全版本】获取用户个人信息 - 正确实现"""
    # 安全：只返回当前登录用户的信息，不接受外部user_id参数
    user = current_user

    return jsonify({
        'code': 200,
        'data': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'id_card': user.id_card[:6] + '********' + user.id_card[-4:],  # 脱敏处理
            'phone': user.phone[:3] + '****' + user.phone[-4:],  # 脱敏处理
            'email': user.email,
            'address': user.address,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@app.route('/api/secure/account/<int:account_id>', methods=['GET'])
@login_required
def api_secure_get_account(account_id):
    """【安全版本】获取账户详情 - 正确实现"""
    # 安全：验证账户是否属于当前用户
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()

    if not account:
        return jsonify({'code': 403, 'msg': '无权访问该账户'}), 403

    transactions = Transaction.query.filter_by(account_id=account_id)\
                    .order_by(Transaction.created_at.desc()).limit(20).all()

    return jsonify({
        'code': 200,
        'data': {
            'id': account.id,
            'account_no': account.account_no,
            'account_type': account.account_type,
            'balance': account.balance,
            'frozen_amount': account.frozen_amount,
            'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'transactions': [{
                'id': t.id,
                'trans_type': t.trans_type,
                'amount': t.amount,
                'balance_after': t.balance_after,
                'description': t.description,
                'target_account': t.target_account,
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for t in transactions]
        }
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
