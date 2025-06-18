// Iron & Steel Business - Frontend JavaScript

// Global variables
let currentUser = null;
let currentToken = null;
let currentLaborRate = 0;
let receiptsToDelete = null;

// API Base URL
const API_BASE_URL = 'https://iron-steel-business.onrender.com/api';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Set current date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('currentDate').textContent = today;
    
    // Set current month for monthly view
    const currentMonth = new Date().toISOString().slice(0, 7);
    document.getElementById('monthYear').value = currentMonth;
    
    // Check if user is already logged in
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');
    
    if (savedToken && savedUser) {
        currentToken = savedToken;
        currentUser = savedUser;
        showMainApp();
        loadDashboard();
        loadLaborRate();
    }
    
    // Setup event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Receipt form
    document.getElementById('receiptForm').addEventListener('submit', handleReceiptSubmit);
    
    // Tab change events
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target === '#dashboard') {
                loadDashboard();
            } else if (target === '#settings') {
                loadLaborRate();
            } else if (target === '#history') {
                loadHistory();
            }
        });
    });
    
    // Dashboard sub-tab events
    document.querySelectorAll('[data-bs-toggle="pill"]').forEach(pill => {
        pill.addEventListener('shown.bs.pill', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target === '#monthly') {
                loadMonthlySummary();
            }
        });
    });

    // Password update form
    document.getElementById('passwordForm').addEventListener('submit', handlePasswordUpdate);
}

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (currentToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${currentToken}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showAlert(error.message, 'danger');
        throw error;
    }
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const data = await apiCall('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        currentToken = data.access_token;
        currentUser = data.username;
        
        // Save to localStorage
        localStorage.setItem('authToken', currentToken);
        localStorage.setItem('currentUser', currentUser);
        
        showMainApp();
        loadDashboard();
        loadLaborRate();
        
        showAlert('Login successful!', 'success');
    } catch (error) {
        showAlert('Login failed. Please check your credentials.', 'danger');
    }
}

function logout() {
    currentToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    document.getElementById('loginPage').classList.remove('d-none');
    document.getElementById('mainApp').classList.add('d-none');
    
    // Clear forms
    document.getElementById('loginForm').reset();
    document.getElementById('receiptForm').reset();
    
    showAlert('Logged out successfully', 'info');
}

function showMainApp() {
    document.getElementById('loginPage').classList.add('d-none');
    document.getElementById('mainApp').classList.remove('d-none');
    document.getElementById('userDisplay').textContent = currentUser;
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const summary = await apiCall('/summary');
        const receipts = await apiCall('/receipts?date=' + new Date().toISOString().split('T')[0]);
        
        updateDashboardSummary(summary);
        updateDashboardTable(receipts);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function updateDashboardSummary(summary) {
    document.getElementById('totalReceipts').textContent = summary.total_receipts;
    document.getElementById('totalWeightToday').textContent = summary.total_weight.toFixed(2);
    document.getElementById('totalLaborCost').textContent = `₹${summary.total_labor_cost.toFixed(2)}`;
    document.getElementById('currentDate').textContent = summary.date;
}

function updateDashboardTable(receipts) {
    const tbody = document.getElementById('dashboardTableBody');
    tbody.innerHTML = '';
    
    if (receipts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No receipts for today</td></tr>';
        return;
    }
    
    receipts.forEach(receipt => {
        const row = document.createElement('tr');
        const itemsText = receipt.items.map(item => {
            let itemText = `${item.item_name} (${item.weight_kg}kg)`;
            if (item.dimension) {
                itemText += ` - ${item.dimension}`;
            }
            return itemText;
        }).join(', ');
        
        row.innerHTML = `
            <td>${receipt.time}</td>
            <td>${receipt.customer_name || '-'}</td>
            <td>${itemsText}</td>
            <td>${receipt.total_weight.toFixed(2)} kg</td>
            <td>₹${receipt.total_labor_cost.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewReceipt(${receipt.id})">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteReceipt(${receipt.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Monthly Summary Functions
async function loadMonthlySummary() {
    const monthYear = document.getElementById('monthYear').value;
    if (!monthYear) return;
    
    const [year, month] = monthYear.split('-');
    
    try {
        const data = await apiCall(`/monthly-summary?year=${year}&month=${month}`);
        updateMonthlySummary(data);
    } catch (error) {
        console.error('Failed to load monthly summary:', error);
    }
}

function updateMonthlySummary(data) {
    document.getElementById('monthlyTotalReceipts').textContent = data.total_receipts;
    document.getElementById('monthlyTotalWeight').textContent = data.total_weight.toFixed(2);
    document.getElementById('monthlyTotalLaborCost').textContent = `₹${data.total_labor_cost.toFixed(2)}`;
    document.getElementById('currentMonth').textContent = `${data.year}-${String(data.month).padStart(2, '0')}`;
    
    // Update daily breakdown table
    const tbody = document.getElementById('monthlyBreakdownBody');
    tbody.innerHTML = '';
    
    if (Object.keys(data.daily_breakdown).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No data for this month</td></tr>';
        return;
    }
    
    // Sort dates
    const sortedDates = Object.keys(data.daily_breakdown).sort();
    
    sortedDates.forEach(date => {
        const dayData = data.daily_breakdown[date];
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${date}</td>
            <td>${dayData.receipts}</td>
            <td>${dayData.weight.toFixed(2)} kg</td>
            <td>₹${dayData.labor_cost.toFixed(2)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Receipt Functions
async function handleReceiptSubmit(e) {
    e.preventDefault();
    
    const items = getFormItems();
    if (items.length === 0) {
        showAlert('Please add at least one item', 'warning');
        return;
    }
    
    const formData = {
        customer_name: document.getElementById('customerName').value,
        notes: document.getElementById('notes').value,
        items: items
    };
    
    try {
        await apiCall('/receipts', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        showAlert('Receipt saved successfully!', 'success');
        document.getElementById('receiptForm').reset();
        clearItemsContainer();
        addItemRow(); // Add one empty row
        
        // Refresh dashboard
        loadDashboard();
    } catch (error) {
        console.error('Failed to save receipt:', error);
    }
}

function getFormItems() {
    const items = [];
    const itemRows = document.querySelectorAll('.item-row');
    
    itemRows.forEach(row => {
        const itemName = row.querySelector('.item-name').value.trim();
        const weight = parseFloat(row.querySelector('.item-weight').value);
        const dimension = row.querySelector('.item-dimension').value.trim();
        
        if (itemName && weight > 0) {
            items.push({
                item_name: itemName,
                weight_kg: weight,
                dimension: dimension
            });
        }
    });
    
    return items;
}

function addItemRow() {
    const container = document.getElementById('itemsContainer');
    const itemRow = document.createElement('div');
    itemRow.className = 'item-row';
    itemRow.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <label class="form-label">Item Name</label>
                <input type="text" class="form-control item-name" placeholder="Enter item name" required>
            </div>
            <div class="col-md-3">
                <label class="form-label">Weight (kg)</label>
                <input type="number" class="form-control item-weight" step="0.01" placeholder="0.00" required onchange="updateFormTotals()">
            </div>
            <div class="col-md-3">
                <label class="form-label">Dimension/Quantity</label>
                <input type="text" class="form-control item-dimension" placeholder="e.g., 8x8 feet, 10 units, 2.5m" onchange="updateFormTotals()">
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger d-block w-100" onclick="removeItemRow(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    container.appendChild(itemRow);
}

function removeItemRow(button) {
    const itemRow = button.closest('.item-row');
    itemRow.remove();
    updateFormTotals();
}

function updateFormTotals() {
    let totalWeight = 0;
    const weightInputs = document.querySelectorAll('.item-weight');
    
    weightInputs.forEach(input => {
        const weight = parseFloat(input.value) || 0;
        totalWeight += weight;
    });
    
    const totalLaborCost = totalWeight * currentLaborRate;
    
    document.getElementById('formTotalWeight').textContent = totalWeight.toFixed(2);
    document.getElementById('formTotalLaborCost').textContent = totalLaborCost.toFixed(2);
}

function clearItemsContainer() {
    document.getElementById('itemsContainer').innerHTML = '';
}

// Labor Rate Functions
async function loadLaborRate() {
    try {
        const data = await apiCall('/labor-rate');
        currentLaborRate = data.rate_per_kg;
        
        document.getElementById('currentRate').textContent = currentLaborRate.toFixed(2);
        document.getElementById('currentRateDisplay').textContent = currentLaborRate.toFixed(2);
        document.getElementById('laborRate').value = currentLaborRate;
    } catch (error) {
        console.error('Failed to load labor rate:', error);
    }
}

async function updateLaborRate() {
    const newRate = parseFloat(document.getElementById('laborRate').value);
    
    if (isNaN(newRate) || newRate < 0) {
        showAlert('Please enter a valid rate', 'warning');
        return;
    }
    
    try {
        await apiCall('/labor-rate', {
            method: 'PUT',
            body: JSON.stringify({ rate_per_kg: newRate })
        });
        
        currentLaborRate = newRate;
        document.getElementById('currentRate').textContent = newRate.toFixed(2);
        document.getElementById('currentRateDisplay').textContent = newRate.toFixed(2);
        
        showAlert('Labor rate updated successfully!', 'success');
    } catch (error) {
        console.error('Failed to update labor rate:', error);
    }
}

// History Functions
async function loadHistory() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const customer = document.getElementById('customerFilter').value;
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    let endpoint = '/receipts?';
    const params = [];
    
    if (startDate && endDate) {
        params.push(`start_date=${startDate}`);
        params.push(`end_date=${endDate}`);
    }
    if (customer) params.push(`customer=${encodeURIComponent(customer)}`);
    params.push(`sort_by=${sortBy}`);
    params.push(`sort_order=${sortOrder}`);
    
    endpoint += params.join('&');
    
    try {
        const receipts = await apiCall(endpoint);
        displayHistory(receipts, startDate, endDate, customer);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function displayHistory(receipts, startDate, endDate, customer) {
    const container = document.getElementById('historyContent');
    
    if (receipts.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No receipts found for the selected criteria.</div>';
        return;
    }
    
    let dateRangeText = '';
    if (startDate && endDate) {
        dateRangeText = `from ${startDate} to ${endDate}`;
    } else if (startDate) {
        dateRangeText = `from ${startDate}`;
    } else if (endDate) {
        dateRangeText = `until ${endDate}`;
    }
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h6>Receipts ${dateRangeText} ${customer ? `- Customer: ${customer}` : ''} (${receipts.length} found)</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Customer</th>
                                <th>Items</th>
                                <th>Total Weight</th>
                                <th>Labor Cost</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    receipts.forEach(receipt => {
        const itemsText = receipt.items.map(item => {
            let itemText = `${item.item_name} (${item.weight_kg}kg)`;
            if (item.dimension) {
                itemText += ` - ${item.dimension}`;
            }
            return itemText;
        }).join(', ');
        
        html += `
            <tr>
                <td>${receipt.date}</td>
                <td>${receipt.time}</td>
                <td>${receipt.customer_name || '-'}</td>
                <td>${itemsText}</td>
                <td>${receipt.total_weight.toFixed(2)} kg</td>
                <td>₹${receipt.total_labor_cost.toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewReceipt(${receipt.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteReceipt(${receipt.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Receipt Actions
async function viewReceipt(receiptId) {
    try {
        const receipts = await apiCall('/receipts');
        const receipt = receipts.find(r => r.id === receiptId);
        
        if (!receipt) {
            showAlert('Receipt not found', 'danger');
            return;
        }
        
        displayReceiptModal(receipt);
    } catch (error) {
        console.error('Failed to load receipt:', error);
    }
}

function displayReceiptModal(receipt) {
    const modalBody = document.getElementById('receiptModalBody');
    const itemsHtml = receipt.items.map(item => {
        let dimensionCell = item.dimension ? `<td>${item.dimension}</td>` : '<td>-</td>';
        return `<tr><td>${item.item_name}</td><td>${item.weight_kg} kg</td>${dimensionCell}<td>₹${item.labor_cost.toFixed(2)}</td></tr>`;
    }).join('');
    
    modalBody.innerHTML = `
        <div class="receipt-print">
            <div class="text-center mb-3">
                <h4>Nav Durga Steel</h4>
                <p class="mb-1">Receipt #${receipt.id}</p>
                <p class="mb-1">Date: ${receipt.date} | Time: ${receipt.time}</p>
                ${receipt.customer_name ? `<p class="mb-1">Customer: ${receipt.customer_name}</p>` : ''}
            </div>
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Weight</th>
                        <th>Dimension/Quantity</th>
                        <th>Labor Cost</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemsHtml}
                </tbody>
                <tfoot>
                    <tr class="table-dark">
                        <th>Total</th>
                        <th>${receipt.total_weight.toFixed(2)} kg</th>
                        <th>-</th>
                        <th>₹${receipt.total_labor_cost.toFixed(2)}</th>
                    </tr>
                </tfoot>
            </table>
            
            ${receipt.notes ? `<p><strong>Notes:</strong> ${receipt.notes}</p>` : ''}
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('receiptModal'));
    modal.show();
}

function deleteReceipt(receiptId) {
    receiptsToDelete = receiptId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

async function confirmDelete() {
    if (!receiptsToDelete) return;
    
    try {
        await apiCall(`/receipts/${receiptsToDelete}`, {
            method: 'DELETE'
        });
        
        showAlert('Receipt deleted successfully!', 'success');
        loadDashboard();
        loadHistory();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        modal.hide();
    } catch (error) {
        console.error('Failed to delete receipt:', error);
    }
}

// Export Functions
async function exportFilteredData() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const customer = document.getElementById('customerFilter').value;
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    let endpoint = '/export?';
    const params = [];
    
    if (startDate && endDate) {
        params.push(`start_date=${startDate}`);
        params.push(`end_date=${endDate}`);
    }
    if (customer) params.push(`customer=${encodeURIComponent(customer)}`);
    params.push(`sort_by=${sortBy}`);
    params.push(`sort_order=${sortOrder}`);
    
    endpoint += params.join('&');
    
    try {
        const data = await apiCall(endpoint);
        downloadCSV(data.content, data.filename);
        showAlert(`Filtered data exported successfully! (${data.total_records} records)`, 'success');
    } catch (error) {
        console.error('Failed to export filtered data:', error);
    }
}

async function exportAllData() {
    try {
        const data = await apiCall('/export');
        downloadCSV(data.content, data.filename);
        showAlert(`All data exported successfully! (${data.total_records} records)`, 'success');
    } catch (error) {
        console.error('Failed to export all data:', error);
    }
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Utility Functions
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function printReceipt() {
    window.print();
}

// Initialize with one item row
document.addEventListener('DOMContentLoaded', function() {
    addItemRow();
});

// Password update handler
async function handlePasswordUpdate(e) {
    e.preventDefault();
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    try {
        const data = await apiCall('/update-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword
            })
        });
        showAlert('Password updated successfully!', 'success');
        document.getElementById('passwordForm').reset();
    } catch (error) {
        // Error message is shown by apiCall
    }
} 