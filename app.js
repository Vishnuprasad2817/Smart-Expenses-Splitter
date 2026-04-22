const API_URL = '/api';
let currentGroupId = null;

// DOM Elements
const views = document.querySelectorAll('.view');
const navItems = document.querySelectorAll('.nav-item');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            switchView(item.dataset.target);
            
            if(item.dataset.target === 'users-view') loadUsers();
            if(item.dataset.target === 'groups-view') loadGroups();
            if(item.dataset.target === 'dashboard-view') loadDashboardStats();
        });
    });
    
    loadDashboardStats();
    
    // Enter key support
    document.getElementById('new-user-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') createUser();
    });
    document.getElementById('new-group-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') createGroup();
    });
    document.getElementById('add-member-select').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') addGroupMember();
    });
});

// View Management
function switchView(viewId) {
    views.forEach(view => view.classList.add('hidden'));
    document.getElementById(viewId).classList.remove('hidden');
}

function switchGroupTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    
    event.target.classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.remove('hidden');
    
    if (tabId === 'expenses') loadGroupExpenses();
    if (tabId === 'balances') loadGroupBalances();
    if (tabId === 'members') loadGroupMembersTab();
}

// Modals
function showModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// API Helpers
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'API Error');
        }
        return await response.json();
    } catch (error) {
        alert(error.message);
        throw error;
    }
}

// --- Dashboard ---
async function loadDashboardStats() {
    try {
        const users = await fetchAPI('/users');
        const groups = await fetchAPI('/groups');
        document.getElementById('stat-users').innerText = users.length;
        document.getElementById('stat-groups').innerText = groups.length;
    } catch(e) {}
}

// --- Users ---
async function loadUsers() {
    const users = await fetchAPI('/users');
    const container = document.getElementById('users-list');
    container.innerHTML = users.map(u => `
        <div class="list-item">
            <span><strong>${u.name}</strong></span>
            <div>
                <button class="btn icon-btn" style="color: #ef4444; border-color: rgba(239, 68, 68, 0.3); padding: 4px 8px;" onclick="deleteUser(${u.id})" title="Delete User"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

async function deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
        await fetchAPI(`/users/${id}`, { method: 'DELETE' });
        loadUsers();
    } catch(e) {
        // API Helper already handles alert
    }
}

async function createUser() {
    const input = document.getElementById('new-user-name');
    const name = input.value.trim();
    if (!name) return alert('Enter a name');
    
    await fetchAPI('/users', { method: 'POST', body: JSON.stringify({ name }) });
    input.value = '';
    loadUsers();
}

// --- Groups ---
async function loadGroups() {
    const groups = await fetchAPI('/groups');
    const container = document.getElementById('groups-list');
    container.innerHTML = groups.map(g => `
        <div class="card glass group-card" onclick="openGroup(${g.id}, '${g.name}')">
            <h3>${g.name}</h3>
            <p>${g.members.length} Members</p>
        </div>
    `).join('');
}

function showCreateGroupModal() {
    document.getElementById('new-group-name').value = '';
    showModal('create-group-modal');
}

async function createGroup() {
    const name = document.getElementById('new-group-name').value.trim();
    if (!name) return alert('Enter group name');
    
    await fetchAPI('/groups', { method: 'POST', body: JSON.stringify({ name }) });
    closeModal('create-group-modal');
    loadGroups();
}

function openGroup(id, name) {
    currentGroupId = id;
    document.getElementById('detail-group-name').innerText = name;
    document.getElementById('detail-group-id').innerText = `Group ID: ${id}`;
    
    // reset UI
    document.getElementById('ai-insights-box').classList.add('hidden');
    switchView('group-detail-view');
    
    // Auto-click first tab
    document.querySelector('.tab').click();
}

// --- Group Details (Members) ---
async function loadGroupMembersTab() {
    const groups = await fetchAPI('/groups');
    const group = groups.find(g => g.id === currentGroupId);
    
    const list = document.getElementById('group-members-list');
    list.innerHTML = group.members.map(m => `<li>${m.name}</li>`).join('');
    
    // Populate select
    const allUsers = await fetchAPI('/users');
    const select = document.getElementById('add-member-select');
    select.innerHTML = '<option value="">Select user...</option>' + 
        allUsers.filter(u => !group.members.some(m => m.id === u.id))
                .map(u => `<option value="${u.id}">${u.name}</option>`).join('');
}

async function addGroupMember() {
    const select = document.getElementById('add-member-select');
    const userId = parseInt(select.value);
    if (!userId) return;
    
    await fetchAPI(`/groups/${currentGroupId}/members`, {
        method: 'POST', body: JSON.stringify({ user_id: userId })
    });
    loadGroupMembersTab();
}

// --- Expenses ---
async function loadGroupExpenses() {
    const expenses = await fetchAPI(`/groups/${currentGroupId}/expenses`);
    const container = document.getElementById('group-expenses-list');
    
    if (expenses.length === 0) {
        container.innerHTML = '<p class="text-muted mt-4">No expenses yet.</p>';
        return;
    }
    
    // We need users to show who paid
    const users = await fetchAPI('/users');
    const userMap = users.reduce((acc, u) => { acc[u.id] = u.name; return acc; }, {});
    
    container.innerHTML = expenses.map(e => `
        <div class="expense-item">
            <div class="expense-info">
                <h4>${e.description} <span class="category-badge">${e.category || 'Unknown'}</span></h4>
                <div class="expense-meta">
                    Paid by ${userMap[e.paid_by] || 'Unknown'} on ${new Date(e.date).toLocaleDateString()}
                </div>
            </div>
            <div class="expense-amount">₹${e.amount.toFixed(2)}</div>
        </div>
    `).join('');
}

async function showAddExpenseModal() {
    const groups = await fetchAPI('/groups');
    const group = groups.find(g => g.id === currentGroupId);
    
    if (group.members.length === 0) {
        alert("Please add members to the group first!");
        return;
    }
    
    const select = document.getElementById('exp-paid-by');
    select.innerHTML = group.members.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
    
    document.getElementById('exp-desc').value = '';
    document.getElementById('exp-amount').value = '';
    
    showModal('add-expense-modal');
}

async function addExpense() {
    const desc = document.getElementById('exp-desc').value.trim();
    const amount = parseFloat(document.getElementById('exp-amount').value);
    const paidBy = parseInt(document.getElementById('exp-paid-by').value);
    
    if (!desc || isNaN(amount) || amount <= 0 || !paidBy) return alert("Invalid inputs");
    
    // Equal split
    const groups = await fetchAPI('/groups');
    const group = groups.find(g => g.id === currentGroupId);
    const splitAmount = amount / group.members.length;
    
    const splits = group.members.map(m => ({
        user_id: m.id,
        amount_owed: splitAmount
    }));
    
    const payload = {
        group_id: currentGroupId,
        description: desc,
        amount: amount,
        paid_by: paidBy,
        splits: splits
    };
    
    const btn = document.querySelector('#add-expense-modal .btn.primary');
    btn.innerText = "Processing AI...";
    btn.disabled = true;
    
    try {
        await fetchAPI(`/groups/${currentGroupId}/expenses`, {
            method: 'POST', body: JSON.stringify(payload)
        });
        closeModal('add-expense-modal');
        loadGroupExpenses();
    } finally {
        btn.innerText = "Save & Categorize (AI)";
        btn.disabled = false;
    }
}

// --- Balances & Settlements ---
async function loadGroupBalances() {
    const data = await fetchAPI(`/groups/${currentGroupId}/balances`);
    
    const balList = document.getElementById('balances-list');
    balList.innerHTML = Object.entries(data.balances).map(([name, bal]) => {
        const isPos = bal > 0;
        const isNeg = bal < 0;
        const colorClass = isPos ? 'positive' : (isNeg ? 'negative' : '');
        const text = isPos ? `gets back ₹${bal.toFixed(2)}` : (isNeg ? `owes ₹${Math.abs(bal).toFixed(2)}` : 'is settled up');
        return `<li><span>${name}</span> <span class="${colorClass}">${text}</span></li>`;
    }).join('');
    
    const setList = document.getElementById('settlements-list');
    if (data.settlements.length === 0) {
        setList.innerHTML = '<p class="text-muted mt-2">Everyone is settled up!</p>';
    } else {
        setList.innerHTML = data.settlements.map(s => `
            <li>
                <div class="settlement-item">
                    <strong>${s.from_user}</strong> 
                    <i class="fas fa-arrow-right" style="color:var(--text-muted); font-size: 0.8rem; margin: 0 5px;"></i> 
                    <strong>${s.to_user}</strong>
                </div>
                <span class="settlement-amount">₹${s.amount.toFixed(2)}</span>
            </li>
        `).join('');
    }
}

// --- AI Features ---
async function getAIInsights() {
    const box = document.getElementById('ai-insights-box');
    box.innerHTML = "<em>Analyzing your group's spending patterns with AI...</em>";
    box.classList.remove('hidden');
    
    try {
        const data = await fetchAPI(`/groups/${currentGroupId}/insights`);
        box.innerHTML = `<strong>✨ AI Insight:</strong> ${data.insight}`;
    } catch (e) {
        box.innerHTML = "<em>Could not load AI insights. Make sure you added your Gemini API Key!</em>";
    }
}

async function generateReply() {
    const msg = document.getElementById('settlement-msg-input').value.trim();
    if (!msg) return;
    
    const output = document.getElementById('ai-reply-output');
    output.innerText = "Generating...";
    
    try {
        const data = await fetchAPI(`/ai/suggest_reply`, {
            method: 'POST', body: JSON.stringify({ message: msg })
        });
        output.innerText = `"${data.reply}"`;
    } catch (e) {
        output.innerText = "Error generating reply.";
    }
}
