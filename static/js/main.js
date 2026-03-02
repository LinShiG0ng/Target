/**
 * 云享财富 - 前端JavaScript
 */

// API请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

// 获取用户个人信息
async function loadProfile(userId = null) {
    let url = '/api/profile';
    if (userId) {
        url += `?user_id=${userId}`;
    }

    try {
        const result = await apiRequest(url);
        if (result.code === 200) {
            displayProfile(result.data);
        } else {
            showError(result.msg);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示个人信息
function displayProfile(data) {
    const container = document.getElementById('profile-container');
    if (!container) return;

    container.innerHTML = `
        <div class="profile-card">
            <div class="profile-avatar">
                <i class="fas fa-user"></i>
            </div>
            <h4 class="text-center mb-4">${data.real_name}</h4>

            <div class="info-item">
                <div class="info-label">用户名</div>
                <div class="info-value">${data.username}</div>
            </div>
            <div class="info-item">
                <div class="info-label">真实姓名</div>
                <div class="info-value">${data.real_name}</div>
            </div>
            <div class="info-item">
                <div class="info-label">身份证号</div>
                <div class="info-value">${data.id_card}</div>
            </div>
            <div class="info-item">
                <div class="info-label">手机号码</div>
                <div class="info-value">${data.phone}</div>
            </div>
            <div class="info-item">
                <div class="info-label">邮箱地址</div>
                <div class="info-value">${data.email || '未设置'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">联系地址</div>
                <div class="info-value">${data.address || '未设置'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">注册时间</div>
                <div class="info-value">${data.created_at}</div>
            </div>
        </div>
    `;
}

// 获取账户详情
async function loadAccountDetail(accountId) {
    try {
        const result = await apiRequest(`/api/account/${accountId}`);
        if (result.code === 200) {
            displayAccountDetail(result.data);
        } else {
            showError(result.msg);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示账户详情
function displayAccountDetail(data) {
    const container = document.getElementById('account-detail-container');
    if (!container) return;

    let transactionHtml = '';
    if (data.transactions && data.transactions.length > 0) {
        transactionHtml = data.transactions.map(t => `
            <div class="transaction-item">
                <div class="transaction-icon ${t.amount >= 0 ? 'income' : 'expense'}">
                    <i class="fas fa-${t.amount >= 0 ? 'arrow-down' : 'arrow-up'}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-medium">${t.description}</div>
                    <small class="text-muted">${t.created_at}</small>
                </div>
                <div class="transaction-amount ${t.amount >= 0 ? 'positive' : 'negative'}">
                    ${t.amount >= 0 ? '+' : ''}${t.amount.toFixed(2)}
                </div>
            </div>
        `).join('');
    } else {
        transactionHtml = '<p class="text-center text-muted py-4">暂无交易记录</p>';
    }

    container.innerHTML = `
        <div class="account-card mb-4">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <span class="badge bg-light text-dark">${data.account_type}</span>
                <span class="account-no">${data.account_no}</span>
            </div>
            <div class="mb-2">
                <small class="opacity-75">可用余额</small>
            </div>
            <div class="balance">¥ ${data.balance.toFixed(2)}</div>
            <div class="mt-2">
                <small class="opacity-75">冻结金额: ¥ ${data.frozen_amount.toFixed(2)}</small>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <i class="fas fa-history me-2"></i>交易记录
            </div>
            <div class="card-body p-0">
                ${transactionHtml}
            </div>
        </div>
    `;
}

// 获取银行卡列表
async function loadCards() {
    try {
        const result = await apiRequest('/api/cards');
        if (result.code === 200) {
            displayCards(result.data);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示银行卡列表
function displayCards(cards) {
    const container = document.getElementById('cards-container');
    if (!container) return;

    if (cards.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-credit-card fa-3x text-muted mb-3"></i>
                <p class="text-muted">您还没有绑定银行卡</p>
                <button class="btn btn-primary"><i class="fas fa-plus me-2"></i>添加银行卡</button>
            </div>
        `;
        return;
    }

    const bankColors = {
        '工商银行': 'card-icbc',
        '建设银行': 'card-ccb',
        '农业银行': 'card-abc',
        '中国银行': 'card-boc'
    };

    container.innerHTML = `
        <div class="row">
            ${cards.map(card => `
                <div class="col-md-6 mb-4">
                    <div class="bank-card ${bankColors[card.bank_name] || ''}" onclick="viewCardDetail(${card.id})" style="cursor:pointer">
                        <div class="d-flex justify-content-between">
                            <span class="fw-bold">${card.bank_name}</span>
                            <span>${card.card_type}</span>
                        </div>
                        <div class="card-number">${card.card_no}</div>
                        <div class="card-info">
                            <span>${card.holder_name}</span>
                            <span>点击查看详情</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// 查看银行卡详情
async function viewCardDetail(cardId) {
    try {
        const result = await apiRequest(`/api/card/${cardId}`);
        if (result.code === 200) {
            showCardModal(result.data);
        } else {
            showError(result.msg);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示银行卡详情模态框
function showCardModal(data) {
    // 移除已有模态框
    const existingModal = document.getElementById('cardDetailModal');
    if (existingModal) {
        existingModal.remove();
    }

    const modalHtml = `
        <div class="modal fade" id="cardDetailModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">银行卡详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="info-item">
                            <div class="info-label">银行卡号</div>
                            <div class="info-value">${data.card_no}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">开户银行</div>
                            <div class="info-value">${data.bank_name}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">卡片类型</div>
                            <div class="info-value">${data.card_type}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">持卡人姓名</div>
                            <div class="info-value">${data.holder_name}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">绑定手机</div>
                            <div class="info-value">${data.bindded_phone}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">绑定时间</div>
                            <div class="info-value">${data.created_at}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('cardDetailModal'));
    modal.show();
}

// 获取消息列表
async function loadMessages() {
    try {
        const result = await apiRequest('/api/messages');
        if (result.code === 200) {
            displayMessages(result.data);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示消息列表
function displayMessages(messages) {
    const container = document.getElementById('messages-container');
    if (!container) return;

    if (messages.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <p class="text-muted">暂无消息</p>
            </div>
        `;
        return;
    }

    const typeClass = {
        '系统通知': 'system',
        '交易提醒': 'transaction',
        '安全提醒': 'security'
    };

    container.innerHTML = `
        <div class="card">
            <div class="card-body p-0">
                ${messages.map(msg => `
                    <div class="message-item ${msg.is_read ? '' : 'unread'}" onclick="viewMessage(${msg.id})">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <span class="message-type ${typeClass[msg.msg_type] || 'system'}">${msg.msg_type}</span>
                                <span class="message-title ms-2">${msg.title}</span>
                            </div>
                            <small class="text-muted">${msg.created_at}</small>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 查看消息详情
async function viewMessage(messageId) {
    try {
        const result = await apiRequest(`/api/message/${messageId}`);
        if (result.code === 200) {
            showMessageModal(result.data);
            // 刷新列表更新已读状态
            loadMessages();
        } else {
            showError(result.msg);
        }
    } catch (error) {
        showError('加载失败');
    }
}

// 显示消息详情模态框
function showMessageModal(data) {
    const existingModal = document.getElementById('messageDetailModal');
    if (existingModal) {
        existingModal.remove();
    }

    const typeClass = {
        '系统通知': 'system',
        '交易提醒': 'transaction',
        '安全提醒': 'security'
    };

    const modalHtml = `
        <div class="modal fade" id="messageDetailModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <span class="message-type ${typeClass[data.msg_type] || 'system'} me-2">${data.msg_type}</span>
                            ${data.title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>${data.content}</p>
                        <hr>
                        <small class="text-muted">发送时间: ${data.created_at}</small>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" onclick="deleteMessage(${data.id})">
                            <i class="fas fa-trash me-2"></i>删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('messageDetailModal'));
    modal.show();
}

// 删除消息
async function deleteMessage(messageId) {
    if (!confirm('确定要删除这条消息吗？')) {
        return;
    }

    try {
        const result = await apiRequest(`/api/message/${messageId}`, {
            method: 'DELETE'
        });

        if (result.code === 200) {
            showSuccess('删除成功');
            const modal = bootstrap.Modal.getInstance(document.getElementById('messageDetailModal'));
            modal.hide();
            loadMessages();
        } else {
            showError(result.msg);
        }
    } catch (error) {
        showError('删除失败');
    }
}

// 显示错误消息
function showError(msg) {
    showToast(msg, 'danger');
}

// 显示成功消息
function showSuccess(msg) {
    showToast(msg, 'success');
}

// 显示Toast消息
function showToast(msg, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${msg}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1100';
    document.body.appendChild(container);
    return container;
}


// 用户搜索（教学演示：用于触发 /api/user/search 请求）
async function runVulnUserSearch(keyword) {
    const result = await apiRequest(`/api/user/search?keyword=${encodeURIComponent(keyword)}`);
    return result;
}

function renderVulnSearchResult(result) {
    const container = document.getElementById('vuln-search-result');
    if (!container) return;

    if (!result || result.code !== 200 || !Array.isArray(result.data) || result.data.length === 0) {
        container.innerHTML = '<span class="text-muted">无匹配用户</span>';
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-sm table-bordered align-middle mb-0">
                <thead class="table-light">
                    <tr>
                        <th>ID</th>
                        <th>用户名</th>
                        <th>姓名</th>
                        <th>手机号</th>
                    </tr>
                </thead>
                <tbody>
                    ${result.data.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.real_name}</td>
                            <td>${user.phone}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function initVulnSearchForm() {
    const form = document.getElementById('vuln-search-form');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const keywordInput = document.getElementById('vuln-search-keyword');
        const keyword = keywordInput ? keywordInput.value : '';

        try {
            const result = await runVulnUserSearch(keyword);
            renderVulnSearchResult(result);
        } catch (error) {
            showError('搜索失败');
        }
    });
}


// 首页模拟接口列表，每个接口对应不同的请求方式和载荷
const HOME_MOCK_ENDPOINTS = [
    { url: '/api/home/banner',        method: 'GET',  body: null },
    { url: '/api/home/announcements', method: 'GET',  body: null },
    { url: '/api/home/products',      method: 'GET',  body: null },
    { url: '/api/home/market',        method: 'GET',  body: null },
    { url: '/api/home/stats',         method: 'GET',  body: null },
    { url: '/api/home/recommend',     method: 'GET',  body: null },
    { url: '/api/home/activities',    method: 'GET',  body: null },
    { url: '/api/home/news',          method: 'GET',  body: null },
    { url: '/api/home/popular',       method: 'GET',  body: null },
    { url: '/api/config/client',      method: 'GET',  body: null },
    {
        url: '/api/track/event', method: 'POST',
        body: () => ({
            event_type: ['page_view', 'scroll', 'click', 'hover', 'heartbeat'][Math.floor(Math.random() * 5)],
            path: window.location.pathname,
            referrer: document.referrer || 'direct',
            ts: new Date().toISOString(),
            session_id: Math.random().toString(36).slice(2),
            meta: { width: window.innerWidth, height: window.innerHeight, language: navigator.language }
        })
    },
    {
        url: '/api/track/pv', method: 'POST',
        body: () => ({
            path: window.location.pathname,
            title: document.title,
            referrer: document.referrer || 'direct',
            ts: new Date().toISOString(),
            uid: Math.random().toString(36).slice(2)
        })
    },
    { url: '/api/noise', method: 'GET',  body: null },
    {
        url: '/api/noise', method: 'POST',
        body: () => ({
            packet_id: `pkt-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            event: 'heartbeat',
            path: window.location.pathname,
            ts: new Date().toISOString()
        })
    },
];

function sendHomeNoiseTraffic() {
    const totalPackets = 80;

    for (let i = 0; i < totalPackets; i++) {
        const endpoint = HOME_MOCK_ENDPOINTS[i % HOME_MOCK_ENDPOINTS.length];
        const bodyData = typeof endpoint.body === 'function' ? endpoint.body() : endpoint.body;

        fetch(endpoint.url, {
            method: endpoint.method,
            headers: { 'Content-Type': 'application/json' },
            body: bodyData ? JSON.stringify(bodyData) : undefined
        }).catch(() => {
            // 噪声流量无需处理错误
        });
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 根据页面自动加载数据
    const path = window.location.pathname;

    // 初始化搜索演示表单（便于前端触发并抓包）
    initVulnSearchForm();

    // 首页打开时批量发送噪声请求，方便抓包
    if (path === '/') {
        sendHomeNoiseTraffic();
    }

    // 账户详情页仍需要异步加载（保留漏洞点）
    if (path.startsWith('/account/')) {
        const accountId = path.split('/').pop();
        loadAccountDetail(accountId);
    }
});
