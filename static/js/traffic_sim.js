/**
 * 云享财富 - 首页流量模拟器
 * 在首页加载时向后台发出多种多样的仿真请求数据包
 */
(function () {
    'use strict';

    // ============================================================
    // 数据池：用于生成各类请求的随机参数
    // ============================================================
    var SEARCH_KEYWORDS = [
        '张', '李', '王', '赵', '陈', '刘', '孙', '周',
        'zhang', 'wang', 'admin', 'user', 'test',
        '张伟', '李娜', '王芳', '赵磊', '陈秀英', '刘洋',
        '1380013', '1591234', '186', '13'
    ];

    var ACCOUNT_NOS = [
        'YX20240101001', 'YX20240101002', 'YX20240101003',
        'YX20240201001', 'YX20240201002', 'YX20240301001',
        'YX20240401001', 'YX20240501001', 'YX20240601002'
    ];

    var TRANSFER_AMOUNTS = [
        50.00, 88.00, 100.00, 128.50, 168.00, 200.00,
        256.88, 300.00, 388.00, 500.00, 520.00, 666.66,
        800.00, 888.00, 1000.00, 1314.00, 1500.00, 1688.00,
        2000.00, 2580.00, 3000.00, 3500.00, 4999.99, 5000.00,
        6800.00, 7777.77, 8888.88, 10000.00, 12000.00, 19999.00
    ];

    var UPDATE_PHONES = [
        '13800138001', '13912345678', '15012345678',
        '15812345678', '15912345678', '18600001234',
        '18711112222', '18999887766', '17612345678'
    ];

    var UPDATE_EMAILS = [
        'zhangwei@qq.com', 'lina123@163.com', 'wangfang@gmail.com',
        'test_user@sina.com', 'admin888@126.com', 'finance@yeah.net',
        'service@yunxiang.com', 'support@fintech.cn'
    ];

    var UPDATE_ADDRESSES = [
        '北京市朝阳区建国路88号',
        '上海市浦东新区陆家嘴金融贸易区',
        '广州市天河区珠江新城花城大道',
        '深圳市南山区科技园南区',
        '杭州市余杭区阿里巴巴西溪园区',
        '成都市高新区天府大道南段',
        '武汉市江汉区解放大道688号'
    ];

    var ECHO_PAYLOADS = [
        '查询账户信息',
        '系统通知测试',
        'hello world',
        '财富增值计划',
        '用户反馈内容',
        '安全验证码1234',
        '理财产品推荐',
        '账单明细查询'
    ];

    // ============================================================
    // 工具函数
    // ============================================================
    function randInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function randItem(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    function shuffle(arr) {
        var a = arr.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
        }
        return a;
    }

    function sleep(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    function randSleep(minMs, maxMs) {
        return sleep(randInt(minMs, maxMs));
    }

    // 生成仿真 X-Request-ID 头
    function genRequestId() {
        var hex = '0123456789abcdef';
        var id = '';
        for (var i = 0; i < 32; i++) {
            id += hex[randInt(0, 15)];
            if (i === 7 || i === 11 || i === 15 || i === 19) id += '-';
        }
        return id;
    }

    // 发送请求（静默忽略结果与错误）
    function fire(url, opts) {
        var options = Object.assign({
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Request-ID': genRequestId()
            }
        }, opts || {});

        // 合并 headers 而非覆盖
        if (opts && opts.headers) {
            options.headers = Object.assign(options.headers, opts.headers);
        }

        fetch(url, options).catch(function () { /* 静默忽略 */ });
    }

    // ============================================================
    // 各类请求发生器
    // ============================================================

    // 1. 批量遍历用户资料（IDOR 场景）
    async function scanProfiles() {
        var ids = shuffle(Array.from({ length: 10 }, function (_, i) { return i + 1; }))
                      .slice(0, randInt(3, 7));
        for (var i = 0; i < ids.length; i++) {
            await randSleep(100, 480);
            fire('/api/profile?user_id=' + ids[i]);
        }
    }

    // 2. 批量遍历账户详情
    async function scanAccounts() {
        var count = randInt(4, 10);
        var visited = new Set();
        for (var i = 0; i < count; i++) {
            var id;
            do { id = randInt(1, 15); } while (visited.has(id));
            visited.add(id);
            await randSleep(130, 650);
            fire('/api/account/' + id);
        }
    }

    // 3. 批量遍历银行卡
    async function scanCards() {
        var count = randInt(3, 8);
        for (var i = 0; i < count; i++) {
            await randSleep(180, 720);
            fire('/api/card/' + randInt(1, 12));
        }
    }

    // 4. 批量遍历站内消息
    async function scanMessages() {
        var count = randInt(5, 14);
        for (var i = 0; i < count; i++) {
            await randSleep(90, 380);
            fire('/api/message/' + randInt(1, 25));
        }
    }

    // 5. 多关键词用户搜索
    async function searchUsers() {
        var kws = shuffle(SEARCH_KEYWORDS).slice(0, randInt(4, 9));
        for (var i = 0; i < kws.length; i++) {
            await randSleep(280, 1100);
            fire('/api/user/search?keyword=' + encodeURIComponent(kws[i]));
        }
    }

    // 6. 获取当前用户卡片列表
    async function getMyCards() {
        await randSleep(150, 400);
        fire('/api/cards');
    }

    // 7. 获取当前用户消息列表
    async function getMyMessages() {
        await randSleep(120, 350);
        fire('/api/messages');
    }

    // 8. 模拟转账请求（跨账户，含余额不足场景）
    async function tryTransfers() {
        var count = randInt(2, 5);
        for (var i = 0; i < count; i++) {
            await randSleep(400, 1800);
            fire('/api/transfer', {
                method: 'POST',
                body: JSON.stringify({
                    from_account_id: randInt(1, 10),
                    to_account_no: randItem(ACCOUNT_NOS),
                    amount: randItem(TRANSFER_AMOUNTS)
                })
            });
        }
    }

    // 9. 模拟篡改他人资料（越权写入）
    async function tryProfileUpdates() {
        var count = randInt(1, 3);
        for (var i = 0; i < count; i++) {
            await randSleep(500, 1400);
            var payload = { user_id: randInt(1, 5) };
            // 随机组合修改字段，更多样
            var r = Math.random();
            if (r < 0.33) {
                payload.phone = randItem(UPDATE_PHONES);
            } else if (r < 0.66) {
                payload.email = randItem(UPDATE_EMAILS);
            } else {
                payload.address = randItem(UPDATE_ADDRESSES);
                payload.phone = randItem(UPDATE_PHONES);
            }
            fire('/api/profile', { method: 'PUT', body: JSON.stringify(payload) });
        }
    }

    // 10. 尝试删除他人消息
    async function tryDeleteMessages() {
        var count = randInt(1, 3);
        for (var i = 0; i < count; i++) {
            await randSleep(600, 2000);
            fire('/api/message/' + randInt(1, 20), { method: 'DELETE' });
        }
    }

    // 11. 访问安全版本端点（对比性流量）
    async function checkSecureEndpoints() {
        await randSleep(200, 700);
        fire('/api/secure/profile');
        await randSleep(300, 900);
        fire('/api/secure/account/' + randInt(1, 8));
    }

    // 12. 访问 echo 端点（模拟正常内容查询）
    async function hitEcho() {
        var payloads = shuffle(ECHO_PAYLOADS).slice(0, randInt(2, 4));
        for (var i = 0; i < payloads.length; i++) {
            await randSleep(150, 500);
            fire('/echo?content=' + encodeURIComponent(payloads[i]));
        }
    }

    // ============================================================
    // 行为模式：模拟不同类型的用户
    // ============================================================
    var BEHAVIOR_PROFILES = [
        // 模式0：普通用户，查看自己的账户
        async function normalUser() {
            await getMyCards();
            await getMyMessages();
            await checkSecureEndpoints();
            await hitEcho();
        },

        // 模式1：好奇用户，轻度尝试查看他人资料
        async function curiousUser() {
            await getMyMessages();
            await scanProfiles();
            await scanAccounts();
            await checkSecureEndpoints();
        },

        // 模式2：搜索型用户，大量关键词搜索
        async function searchHeavyUser() {
            await searchUsers();
            await scanProfiles();
            await getMyCards();
        },

        // 模式3：激进 IDOR 扫描器
        async function aggressiveScanner() {
            await scanProfiles();
            await scanAccounts();
            await scanCards();
            await scanMessages();
            await searchUsers();
        },

        // 模式4：转账攻击者
        async function transferAttacker() {
            await scanAccounts();
            await tryTransfers();
            await tryProfileUpdates();
        },

        // 模式5：消息攻击者（读取+删除他人消息）
        async function messageAttacker() {
            await scanMessages();
            await tryDeleteMessages();
            await scanProfiles();
        },

        // 模式6：混合行为（综合多种操作）
        async function mixedBehavior() {
            await getMyCards();
            await searchUsers();
            await scanAccounts();
            await tryTransfers();
            await scanCards();
            await getMyMessages();
        },

        // 模式7：资料篡改者
        async function profileTamperer() {
            await scanProfiles();
            await tryProfileUpdates();
            await checkSecureEndpoints();
            await hitEcho();
        }
    ];

    // ============================================================
    // 启动：并发多个"用户会话"
    // ============================================================
    async function startSimulation() {
        // 随机选取 4~7 个并发会话，每个选不同的行为模式
        var sessionCount = randInt(4, 7);
        var profiles = shuffle(BEHAVIOR_PROFILES.slice()).slice(0, sessionCount);
        var sessions = profiles.map(function (profile) {
            // 各会话有不同的启动延迟，模拟真实用户陆续到达
            var startDelay = randInt(0, 2000);
            return sleep(startDelay).then(function () { return profile(); });
        });

        Promise.allSettled(sessions);
    }

    // 页面加载完成后，延迟 500ms 启动（避免阻塞首屏渲染）
    document.addEventListener('DOMContentLoaded', function () {
        setTimeout(startSimulation, 500);
    });

})();
