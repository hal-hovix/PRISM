// PRISM v2.0.0 - モダンなWeb UI JavaScript

const API = (window.API_BASE_URL || 'http://localhost:8060');
const API_KEY = 'your-secure-api-key-here'; // 実際のAPIキーに置き換え

// タブ切り替え機能
function initTabs() {
  const navLinks = document.querySelectorAll('.nav-link');
  const tabContents = document.querySelectorAll('.tab-content');

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      
      // アクティブなタブを更新
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      
      // コンテンツを切り替え
      const targetTab = link.getAttribute('data-tab');
      tabContents.forEach(content => {
        content.classList.remove('active');
        if (content.id === targetTab) {
          content.classList.add('active');
        }
      });
      
      // モバイルメニューを閉じる
      closeMobileMenu();
    });
  });
}

// モバイルメニュー機能
function initMobileMenu() {
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const nav = document.getElementById('nav');
  
  if (mobileMenuToggle && nav) {
    mobileMenuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMobileMenu();
    });
    
    // メニュー外をクリックしたら閉じる
    document.addEventListener('click', (e) => {
      if (!nav.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
        closeMobileMenu();
      }
    });
    
    // ESCキーでメニューを閉じる
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeMobileMenu();
      }
    });
  }
}

function toggleMobileMenu() {
  const nav = document.getElementById('nav');
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  
  if (nav && mobileMenuToggle) {
    nav.classList.toggle('active');
    
    // アイコンを変更
    const icon = mobileMenuToggle.querySelector('i');
    if (nav.classList.contains('active')) {
      icon.className = 'fas fa-times';
    } else {
      icon.className = 'fas fa-bars';
    }
  }
}

function closeMobileMenu() {
  const nav = document.getElementById('nav');
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  
  if (nav && mobileMenuToggle) {
    nav.classList.remove('active');
    
    // アイコンを戻す
    const icon = mobileMenuToggle.querySelector('i');
    icon.className = 'fas fa-bars';
  }
}

// タッチイベントの最適化
function initTouchOptimization() {
  // ダブルタップズームを無効化
  let lastTouchEnd = 0;
  document.addEventListener('touchend', (e) => {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
      e.preventDefault();
    }
    lastTouchEnd = now;
  }, false);
  
  // タッチフィードバック
  document.addEventListener('touchstart', (e) => {
    if (e.target.classList.contains('btn') || e.target.classList.contains('nav-link')) {
      e.target.style.transform = 'scale(0.95)';
    }
  });
  
  document.addEventListener('touchend', (e) => {
    if (e.target.classList.contains('btn') || e.target.classList.contains('nav-link')) {
      setTimeout(() => {
        e.target.style.transform = '';
      }, 150);
    }
  });
}

// 画面サイズ変更時の処理
function initResponsiveHandling() {
  let resizeTimeout;
  
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      // デスクトップサイズになったらモバイルメニューを閉じる
      if (window.innerWidth > 768) {
        closeMobileMenu();
      }
    }, 250);
  });
}

// 検索フォーム
function initSearchForm() {
  const form = document.getElementById('query-form');
  const resultsDiv = document.getElementById('results');

  form.addEventListener('submit', async (e) => {
  e.preventDefault();
    
    const formData = new FormData(form);
    const query = formData.get('q');
    const type = formData.get('type');
    const tag = formData.get('tag');
    const semanticSearch = document.getElementById('semantic-search').checked;
    const limit = document.getElementById('search-limit').value;
    
    if (!query.trim()) {
      resultsDiv.innerHTML = '<div class="error">検索キーワードを入力してください。</div>';
      return;
    }

    try {
      resultsDiv.textContent = '検索中...';
      resultsDiv.classList.add('loading');
      
      let response;
      
      if (semanticSearch) {
        // セマンティック検索
        const dbTypes = type ? type : 'Task,ToDo,Knowledge,Note';
        response = await fetch(`${API}/search/semantic?query=${encodeURIComponent(query)}&database_types=${encodeURIComponent(dbTypes)}&limit=${limit}`, {
          headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
          }
        });
      } else {
        // 従来の検索
  const params = new URLSearchParams();
        if (query) params.set('q', query);
  if (type) params.set('type', type);
  if (tag) params.set('tag', tag);
        
        response = await fetch(`${API}/query?${params.toString()}`, {
          headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || '検索に失敗しました');
      }
      
      resultsDiv.classList.remove('loading');
      
      if (semanticSearch) {
        displaySemanticResults(data);
      } else {
        displayResults(data);
      }
      
    } catch (error) {
      resultsDiv.classList.remove('loading');
      resultsDiv.innerHTML = `<div class="error">エラー: ${error.message}</div>`;
    }
  });
}

// セマンティック検索結果の表示
function displaySemanticResults(data) {
  const resultsDiv = document.getElementById('results');
  
  let html = `
    <div class="search-info">
      <h3>検索結果</h3>
      <p><strong>クエリ:</strong> "${data.query}"</p>
      <p><strong>拡張キーワード:</strong> ${data.expanded_keywords.join(', ')}</p>
      <p><strong>結果数:</strong> ${data.total_count}件 (${data.search_time_ms}ms)</p>
    </div>
  `;
  
  if (data.results && data.results.length > 0) {
    html += '<div class="search-results">';
    
    data.results.forEach((item, index) => {
      const relevancePercent = Math.round(item.relevance_score * 100);
      const relevanceColor = relevancePercent >= 80 ? '#28a745' : 
                            relevancePercent >= 60 ? '#ffc107' : '#dc3545';
      
      html += `
        <div class="search-result-item" data-item-id="${item.id}">
          <div class="result-header">
            <h4 class="result-title">${item.title || 'タイトルなし'}</h4>
            <div class="result-meta">
              <span class="result-database">${item.database}</span>
              <span class="result-relevance" style="color: ${relevanceColor}">
                関連度: ${relevancePercent}%
              </span>
            </div>
          </div>
          <div class="result-content">
            <p>${item.content || '内容なし'}</p>
          </div>
          <div class="result-actions">
            <button class="btn btn-sm btn-outline" onclick="getRelatedItems('${item.id}')">
              <i class="fas fa-link"></i> 関連アイテム
            </button>
            <span class="result-date">
              ${new Date(item.created_time).toLocaleDateString('ja-JP')}
            </span>
          </div>
        </div>
      `;
    });
    
    html += '</div>';
  } else {
    html += '<div class="no-results">該当する結果が見つかりませんでした。</div>';
  }
  
  resultsDiv.innerHTML = html;
}

// 従来の検索結果表示
function displayResults(data) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

// 関連アイテムを取得
async function getRelatedItems(itemId) {
  try {
    const response = await fetch(`${API}/search/related/${itemId}?limit=5`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || '関連アイテムの取得に失敗しました');
    }
    
    displayRelatedItems(itemId, data.related_items);
    
  } catch (error) {
    showNotification(`関連アイテムの取得に失敗: ${error.message}`, 'error');
  }
}

// 関連アイテムを表示
function displayRelatedItems(itemId, relatedItems) {
  const resultItem = document.querySelector(`[data-item-id="${itemId}"]`);
  if (!resultItem) return;
  
  let existingRelated = resultItem.querySelector('.related-items');
  if (existingRelated) {
    existingRelated.remove();
    return;
  }
  
  let html = '<div class="related-items"><h5>関連アイテム:</h5>';
  
  if (relatedItems && relatedItems.length > 0) {
    html += '<ul class="related-list">';
    relatedItems.forEach(item => {
      const relevancePercent = Math.round(item.relevance_score * 100);
      html += `
        <li class="related-item">
          <a href="#" onclick="highlightItem('${item.id}'); return false;">
            <strong>${item.title || 'タイトルなし'}</strong>
            <span class="related-database">(${item.database})</span>
            <span class="related-relevance">${relevancePercent}%</span>
          </a>
        </li>
      `;
    });
    html += '</ul>';
  } else {
    html += '<p class="no-related">関連アイテムが見つかりませんでした。</p>';
  }
  
  html += '</div>';
  
  resultItem.insertAdjacentHTML('beforeend', html);
}

// アイテムをハイライト
function highlightItem(itemId) {
  // 既存のハイライトを削除
  document.querySelectorAll('.highlighted').forEach(el => {
    el.classList.remove('highlighted');
  });
  
  // 新しいアイテムをハイライト
  const item = document.querySelector(`[data-item-id="${itemId}"]`);
  if (item) {
    item.classList.add('highlighted');
    item.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// 分類フォーム
function initClassifyForm() {
  const form = document.getElementById('classify-form');
  const resultsDiv = document.getElementById('classify-out');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
  const title = document.getElementById('title').value;
  const body = document.getElementById('body').value;
    
    if (!title.trim()) {
      alert('タイトルを入力してください');
      return;
    }
    
  const payload = { items: [{ title, body }] };

    try {
      resultsDiv.textContent = '分類中...';
      resultsDiv.classList.add('loading');
      
      const response = await fetch(`${API}/classify`, {
    method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        },
    body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      resultsDiv.textContent = JSON.stringify(data, null, 2);
      resultsDiv.classList.remove('loading');
      
      // フォームをクリア
      form.reset();
      
    } catch (error) {
      resultsDiv.textContent = `エラー: ${error.message}`;
      resultsDiv.classList.remove('loading');
    }
  });
}

// 監視ダッシュボード
function initMonitoring() {
  const refreshBtn = document.getElementById('refresh-metrics');
  
  // 初期読み込み
  updateMetrics();
  
  // 更新ボタン
  refreshBtn.addEventListener('click', updateMetrics);
  
  // 自動更新（30秒間隔）
  setInterval(updateMetrics, 30000);
}

async function updateMetrics() {
  try {
    // API ステータスチェック
    await checkApiStatus();
    
    // システム情報取得
    await getSystemInfo();
    
    // レスポンス時間測定
    await measureResponseTime();
    
  } catch (error) {
    console.error('メトリクス更新エラー:', error);
  }
}

async function checkApiStatus() {
  const statusDiv = document.getElementById('api-status');
  const statusDot = statusDiv.querySelector('.status-dot');
  const statusText = statusDiv.querySelector('.status-text');
  
  try {
    const startTime = Date.now();
    const response = await fetch(`${API}/healthz`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    });
    const responseTime = Date.now() - startTime;
    
    if (response.ok) {
      statusDot.className = 'status-dot healthy';
      statusText.textContent = `正常 (${responseTime}ms)`;
    } else {
      statusDot.className = 'status-dot warning';
      statusText.textContent = `警告 (HTTP ${response.status})`;
    }
  } catch (error) {
    statusDot.className = 'status-dot error';
    statusText.textContent = `エラー: ${error.message}`;
  }
}

async function getSystemInfo() {
  const cpuUsage = document.getElementById('cpu-usage');
  const memoryUsage = document.getElementById('memory-usage');
  
  try {
    const response = await fetch(`${API}/healthz/detailed`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      const system = data.system;
      
      cpuUsage.textContent = `${system.cpu.percent.toFixed(1)}%`;
      memoryUsage.textContent = `${system.memory.percent.toFixed(1)}%`;
      
      // 色分け
      if (system.cpu.percent > 80) {
        cpuUsage.style.color = 'var(--warning-color)';
      } else if (system.cpu.percent > 95) {
        cpuUsage.style.color = 'var(--error-color)';
      } else {
        cpuUsage.style.color = 'var(--success-color)';
      }
      
      if (system.memory.percent > 80) {
        memoryUsage.style.color = 'var(--warning-color)';
      } else if (system.memory.percent > 95) {
        memoryUsage.style.color = 'var(--error-color)';
      } else {
        memoryUsage.style.color = 'var(--success-color)';
      }
    }
  } catch (error) {
    cpuUsage.textContent = 'エラー';
    memoryUsage.textContent = 'エラー';
    cpuUsage.style.color = 'var(--error-color)';
    memoryUsage.style.color = 'var(--error-color)';
  }
}

async function measureResponseTime() {
  const timeValue = document.querySelector('.time-value');
  
  try {
    const startTime = Date.now();
    const response = await fetch(`${API}/healthz`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    });
    const responseTime = Date.now() - startTime;
    
    timeValue.textContent = responseTime;
    
    // 色分け
    if (responseTime > 1000) {
      timeValue.style.color = 'var(--error-color)';
    } else if (responseTime > 500) {
      timeValue.style.color = 'var(--warning-color)';
    } else {
      timeValue.style.color = 'var(--success-color)';
    }
    
  } catch (error) {
    timeValue.textContent = 'エラー';
    timeValue.style.color = 'var(--error-color)';
  }
}

// ユーティリティ関数
function showNotification(message, type = 'info') {
  // 簡単な通知表示（将来的にはより高度な通知システムに置き換え可能）
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background: var(--surface-color);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 1000;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// CSS アニメーションを動的に追加
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style);

// 分析機能
function initAnalytics() {
  const refreshBtn = document.getElementById('refresh-analytics');
  const periodSelect = document.getElementById('analytics-period');

  // 分析データ更新
  async function updateAnalytics() {
    const period = periodSelect.value;
    
    try {
      // 分析データを取得
      const response = await fetch(`${API}/analytics/overview?days=${period}`, {
        headers: {
          'Authorization': `Bearer ${API_KEY}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // タスク完了統計を更新
      updateTaskStats(data.task_stats);
      
      // カテゴリ分布を更新
      updateCategoryDistribution(data.category_distribution);
      
      // 時間分析を更新
      updateTimeAnalysis(data.time_analysis);
      
      // 習慣・知識を更新
      updateHabitKnowledge(data.habit_completion_rate, data.knowledge_growth);

    } catch (error) {
      console.error('分析データ取得エラー:', error);
      showAnalyticsError();
    }
  }

  // タスク統計更新
  function updateTaskStats(stats) {
    document.getElementById('total-tasks').textContent = stats.total_tasks;
    document.getElementById('completed-tasks').textContent = stats.completed_tasks;
    document.getElementById('completion-rate').textContent = `${stats.completion_rate}%`;
    document.getElementById('overdue-tasks').textContent = stats.overdue_tasks;
  }

  // カテゴリ分布更新
  function updateCategoryDistribution(categories) {
    const container = document.getElementById('category-chart');
    
    if (categories.length === 0) {
      container.innerHTML = '<div class="chart-placeholder">カテゴリデータがありません</div>';
      return;
    }

    const html = categories.map(cat => `
      <div class="category-item">
        <span class="category-name">${cat.category}</span>
        <div>
          <span class="category-count">${cat.count}</span>
          <span class="category-percentage">(${cat.percentage}%)</span>
        </div>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  // 時間分析更新
  function updateTimeAnalysis(timeData) {
    const container = document.getElementById('time-chart');
    
    if (timeData.length === 0) {
      container.innerHTML = '<div class="chart-placeholder">時間分析データがありません</div>';
      return;
    }

    // 最新の7日間のみ表示
    const recentData = timeData.slice(0, 7);
    
    const html = recentData.map(item => `
      <div class="time-analysis-item">
        <span class="time-period">${item.period}</span>
        <div class="time-stats">
          <span class="time-stat created">作成: ${item.tasks_created}</span>
          <span class="time-stat completed">完了: ${item.tasks_completed}</span>
          <span class="time-stat rate">${item.completion_rate}%</span>
        </div>
      </div>
    `).join('');

    container.innerHTML = html;
  }

  // 習慣・知識更新
  function updateHabitKnowledge(habitRate, knowledgeGrowth) {
    document.getElementById('habit-completion').textContent = `${habitRate}%`;
    document.getElementById('knowledge-growth').textContent = knowledgeGrowth;
  }

  // エラー表示
  function showAnalyticsError() {
    const containers = ['category-chart', 'time-chart'];
    containers.forEach(id => {
      const container = document.getElementById(id);
      container.innerHTML = '<div class="chart-placeholder">データの取得に失敗しました</div>';
    });
    
    // 統計値もエラー表示
    const statIds = ['total-tasks', 'completed-tasks', 'completion-rate', 'overdue-tasks', 'habit-completion', 'knowledge-growth'];
    statIds.forEach(id => {
      document.getElementById(id).textContent = '-';
    });
  }

  // イベントリスナー
  if (refreshBtn) {
    refreshBtn.addEventListener('click', updateAnalytics);
  }
  if (periodSelect) {
    periodSelect.addEventListener('change', updateAnalytics);
  }

  // 初期読み込み
  updateAnalytics();
}

// AIアシスタント機能
function initAssistant() {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  
  // 初期時刻を設定
  const initialTime = document.getElementById('initial-time');
  if (initialTime) {
    initialTime.textContent = new Date().toLocaleTimeString('ja-JP');
  }
  
  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const message = chatInput.value.trim();
      if (!message) return;
      
      // ユーザーメッセージを表示
      addMessage('user', message);
      chatInput.value = '';
      
      // タイピングインジケーターを表示
      showTypingIndicator();
      
      try {
        // AIアシスタントにメッセージを送信
        const response = await fetch(`${API}/assistant/chat?message=${encodeURIComponent(message)}`, {
          headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        
        // タイピングインジケーターを削除
        hideTypingIndicator();
        
        if (response.ok) {
          // AIの応答を表示
          addMessage('assistant', data.message);
        } else {
          addMessage('assistant', `エラー: ${data.detail || 'AIアシスタントとの通信に失敗しました'}`);
        }
        
      } catch (error) {
        hideTypingIndicator();
        addMessage('assistant', `エラー: ${error.message}`);
      }
    });
    
    // Enterキーで送信（Shift+Enterで改行）
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });
  }
}

// メッセージを追加
function addMessage(role, content) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}-message`;
  
  const icon = role === 'user' ? 'fas fa-user' : 'fas fa-robot';
  const time = new Date().toLocaleTimeString('ja-JP');
  
  messageDiv.innerHTML = `
    <div class="message-content">
      <i class="${icon}"></i>
      <p>${content}</p>
    </div>
    <div class="message-time">${time}</div>
  `;
  
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// タイピングインジケーターを表示
function showTypingIndicator() {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message assistant-message typing-indicator';
  typingDiv.id = 'typing-indicator';
  
  typingDiv.innerHTML = `
    <div class="message-content">
      <i class="fas fa-robot"></i>
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
  
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// タイピングインジケーターを削除
function hideTypingIndicator() {
  const typingIndicator = document.getElementById('typing-indicator');
  if (typingIndicator) {
    typingIndicator.remove();
  }
}

// クイックアクション関数
async function askProductivityInsights() {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.value = '生産性の洞察を教えてください';
    chatInput.dispatchEvent(new Event('input'));
    
    // フォームを送信
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
      chatForm.dispatchEvent(new Event('submit'));
    }
  }
}

async function askTaskStatus() {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.value = '現在のタスクの状況を教えてください';
    chatInput.dispatchEvent(new Event('input'));
    
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
      chatForm.dispatchEvent(new Event('submit'));
    }
  }
}

async function askHabitProgress() {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.value = '習慣の進捗状況を教えてください';
    chatInput.dispatchEvent(new Event('input'));
    
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
      chatForm.dispatchEvent(new Event('submit'));
    }
  }
}

function clearChat() {
  const chatMessages = document.getElementById('chat-messages');
  if (chatMessages) {
    chatMessages.innerHTML = `
      <div class="message assistant-message">
        <div class="message-content">
          <i class="fas fa-robot"></i>
          <p>こんにちは！私はPRISMのAIアシスタントです。タスク管理、習慣追跡、知識管理について何でもお聞きください。どのようにお手伝いできますか？</p>
        </div>
        <div class="message-time">${new Date().toLocaleTimeString('ja-JP')}</div>
      </div>
    `;
  }
}

// レポート機能
function initReports() {
  const reportTypeSelect = document.getElementById('report-type');
  const customDates = document.getElementById('custom-dates');
  const customEndDate = document.getElementById('custom-end-date');
  const generateBtn = document.getElementById('generate-report');
  const downloadBtn = document.getElementById('download-report');
  const reportPreview = document.getElementById('report-preview');
  const reportLoading = document.getElementById('report-loading');
  
  // レポートタイプ変更時の処理
  if (reportTypeSelect) {
    reportTypeSelect.addEventListener('change', (e) => {
      const isCustom = e.target.value === 'custom';
      customDates.style.display = isCustom ? 'block' : 'none';
      customEndDate.style.display = isCustom ? 'block' : 'none';
    });
  }
  
  // レポート生成
  if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
      await generateReport();
    });
  }
  
  // レポートダウンロード
  if (downloadBtn) {
    downloadBtn.addEventListener('click', () => {
      downloadReport();
    });
  }
}

// レポート生成
async function generateReport() {
  const reportType = document.getElementById('report-type').value;
  const template = document.getElementById('report-template').value;
  const reportPreview = document.getElementById('report-preview');
  const reportLoading = document.getElementById('report-loading');
  const generateBtn = document.getElementById('generate-report');
  const downloadBtn = document.getElementById('download-report');
  
  // UI状態を更新
  generateBtn.disabled = true;
  reportPreview.style.display = 'none';
  reportLoading.style.display = 'block';
  
  try {
    let url = '';
    let params = new URLSearchParams();
    
    if (reportType === 'weekly') {
      url = `${API}/reports/weekly`;
    } else if (reportType === 'monthly') {
      url = `${API}/reports/monthly`;
    } else if (reportType === 'custom') {
      const startDate = document.getElementById('start-date').value;
      const endDate = document.getElementById('end-date').value;
      
      if (!startDate || !endDate) {
        throw new Error('カスタムレポートには開始日と終了日が必要です');
      }
      
      url = `${API}/reports/custom`;
      params.set('start_date', startDate);
      params.set('end_date', endDate);
      params.set('template', template);
    }
    
    const response = await fetch(`${url}?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'レポート生成に失敗しました');
    }
    
    // レポートを表示
    displayReport(data);
    
  } catch (error) {
    console.error('Report generation error:', error);
    showReportError(error.message);
  } finally {
    generateBtn.disabled = false;
    reportLoading.style.display = 'none';
  }
}

// レポート表示
function displayReport(data) {
  const reportPreview = document.getElementById('report-preview');
  const reportTitle = document.getElementById('report-title');
  const reportPeriod = document.getElementById('report-period');
  const reportGeneratedAt = document.getElementById('report-generated-at');
  const reportContent = document.getElementById('report-content');
  const downloadBtn = document.getElementById('download-report');
  
  // ヘッダー情報を設定
  reportTitle.textContent = `${data.report_type === 'weekly' ? '週次' : data.report_type === 'monthly' ? '月次' : 'カスタム'}レポート`;
  reportPeriod.textContent = `期間: ${data.period}`;
  reportGeneratedAt.textContent = `生成日時: ${new Date(data.generated_at).toLocaleString('ja-JP')}`;
  
  // レポート内容を設定
  reportContent.innerHTML = formatReportContent(data.content);
  
  // UIを表示
  reportPreview.style.display = 'block';
  downloadBtn.style.display = 'inline-block';
  
  // レポートデータを保存（ダウンロード用）
  window.currentReport = data;
  
  // レポートプレビューにスクロール
  reportPreview.scrollIntoView({ behavior: 'smooth' });
}

// レポート内容のフォーマット
function formatReportContent(content) {
  // 改行を<br>に変換
  let formatted = content.replace(/\n/g, '<br>');
  
  // 見出しを検出してフォーマット
  formatted = formatted.replace(/(\d+\.\s*[^<]+)/g, '<h4>$1</h4>');
  
  // リスト項目を検出してフォーマット
  formatted = formatted.replace(/([-•]\s*[^<]+)/g, '<li>$1</li>');
  
  // リスト項目を<ul>で囲む
  formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  
  return formatted;
}

// レポートエラー表示
function showReportError(message) {
  const reportPreview = document.getElementById('report-preview');
  const reportContent = document.getElementById('report-content');
  
  reportContent.innerHTML = `
    <div class="error">
      <h4>エラー</h4>
      <p>${message}</p>
    </div>
  `;
  
  reportPreview.style.display = 'block';
}

// レポートダウンロード
function downloadReport() {
  if (!window.currentReport) {
    alert('ダウンロードするレポートがありません');
    return;
  }
  
  const report = window.currentReport;
  const filename = `prism-report-${report.report_type}-${new Date().toISOString().split('T')[0]}.txt`;
  
  // レポート内容をテキスト形式で準備
  const content = `
PRISM ${report.report_type === 'weekly' ? '週次' : report.report_type === 'monthly' ? '月次' : 'カスタム'}レポート

期間: ${report.period}
生成日時: ${new Date(report.generated_at).toLocaleString('ja-JP')}

${report.content}

---
PRISM v2.0.0 - Personalized Recommendation and Intelligent System for Management
  `.trim();
  
  // ダウンロード実行
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// 通知機能
function initNotifications() {
  const settingsForm = document.getElementById('notification-settings-form');
  const loadSettingsBtn = document.getElementById('load-settings');
  const testEmailBtn = document.getElementById('test-email');
  const testSlackBtn = document.getElementById('test-slack');
  const testSystemBtn = document.getElementById('test-system');
  const testResults = document.getElementById('test-results');
  const notificationStatus = document.getElementById('notification-status');
  
  // 設定フォームの送信
  if (settingsForm) {
    settingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await saveNotificationSettings();
    });
  }
  
  // 設定読み込み
  if (loadSettingsBtn) {
    loadSettingsBtn.addEventListener('click', async () => {
      await loadNotificationSettings();
    });
  }
  
  // テストボタン
  if (testEmailBtn) {
    testEmailBtn.addEventListener('click', async () => {
      await testEmailNotification();
    });
  }
  
  if (testSlackBtn) {
    testSlackBtn.addEventListener('click', async () => {
      await testSlackNotification();
    });
  }
  
  if (testSystemBtn) {
    testSystemBtn.addEventListener('click', async () => {
      await testSystemAlert();
    });
  }
  
  // 初期読み込み
  loadNotificationSettings();
  updateNotificationStatus();
}

// 通知設定を保存
async function saveNotificationSettings() {
  try {
    const settings = {
      email_enabled: document.getElementById('email-enabled').checked,
      email_frequency: document.getElementById('email-frequency').value,
      email_time: document.getElementById('email-time').value,
      slack_enabled: document.getElementById('slack-enabled').checked,
      slack_webhook_url: document.getElementById('slack-webhook-url').value,
      slack_channel: document.getElementById('slack-channel').value,
      task_reminders: document.getElementById('task-reminders').checked,
      habit_notifications: document.getElementById('habit-notifications').checked,
      system_alerts: document.getElementById('system-alerts').checked
    };
    
    const response = await fetch(`${API}/notifications/settings`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showNotification('通知設定を保存しました', 'success');
      updateNotificationStatus();
    } else {
      throw new Error(data.detail || '設定の保存に失敗しました');
    }
    
  } catch (error) {
    console.error('Error saving notification settings:', error);
    showNotification(`設定の保存に失敗: ${error.message}`, 'error');
  }
}

// 通知設定を読み込み
async function loadNotificationSettings() {
  try {
    const response = await fetch(`${API}/notifications/settings`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      const settings = data.settings;
      
      // フォームに設定を反映
      document.getElementById('email-enabled').checked = settings.email_enabled;
      document.getElementById('email-frequency').value = settings.email_frequency;
      document.getElementById('email-time').value = settings.email_time;
      document.getElementById('slack-enabled').checked = settings.slack_enabled;
      document.getElementById('slack-webhook-url').value = settings.slack_webhook_url || '';
      document.getElementById('slack-channel').value = settings.slack_channel || '';
      document.getElementById('task-reminders').checked = settings.task_reminders;
      document.getElementById('habit-notifications').checked = settings.habit_notifications;
      document.getElementById('system-alerts').checked = settings.system_alerts;
      
      showNotification('通知設定を読み込みました', 'success');
    } else {
      throw new Error(data.detail || '設定の読み込みに失敗しました');
    }
    
  } catch (error) {
    console.error('Error loading notification settings:', error);
    showNotification(`設定の読み込みに失敗: ${error.message}`, 'error');
  }
}

// メール通知テスト
async function testEmailNotification() {
  try {
    addTestResult('メール通知テストを開始...', 'info');
    
    const response = await fetch(`${API}/notifications/test/email`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      addTestResult('✅ メール通知テストが成功しました', 'success');
    } else {
      addTestResult(`❌ メール通知テストが失敗しました: ${data.message}`, 'error');
    }
    
  } catch (error) {
    console.error('Error testing email notification:', error);
    addTestResult(`❌ メール通知テストでエラーが発生しました: ${error.message}`, 'error');
  }
}

// Slack通知テスト
async function testSlackNotification() {
  try {
    addTestResult('Slack通知テストを開始...', 'info');
    
    const response = await fetch(`${API}/notifications/test/slack`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      addTestResult('✅ Slack通知テストが成功しました', 'success');
    } else {
      addTestResult(`❌ Slack通知テストが失敗しました: ${data.message}`, 'error');
    }
    
  } catch (error) {
    console.error('Error testing Slack notification:', error);
    addTestResult(`❌ Slack通知テストでエラーが発生しました: ${error.message}`, 'error');
  }
}

// システムアラートテスト
async function testSystemAlert() {
  try {
    addTestResult('システムアラートテストを開始...', 'info');
    
    const response = await fetch(`${API}/notifications/system-alert?alert_type=テスト&message=これはPRISMのシステムアラートテストです`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      addTestResult('✅ システムアラートテストが成功しました', 'success');
    } else {
      addTestResult(`❌ システムアラートテストが失敗しました: ${data.message}`, 'error');
    }
    
  } catch (error) {
    console.error('Error testing system alert:', error);
    addTestResult(`❌ システムアラートテストでエラーが発生しました: ${error.message}`, 'error');
  }
}

// テスト結果を追加
function addTestResult(message, type) {
  const testResults = document.getElementById('test-results');
  if (!testResults) return;
  
  const resultDiv = document.createElement('div');
  resultDiv.className = `test-result ${type}`;
  resultDiv.textContent = `${new Date().toLocaleTimeString('ja-JP')} - ${message}`;
  
  testResults.appendChild(resultDiv);
  testResults.scrollTop = testResults.scrollHeight;
}

// 通知ステータスを更新
async function updateNotificationStatus() {
  try {
    const response = await fetch(`${API}/notifications/test`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      const statusDiv = document.getElementById('notification-status');
      if (statusDiv) {
        const results = data.test_results;
        
        statusDiv.innerHTML = `
          <div class="status-item">
            <h5>メール通知</h5>
            <div class="status-value ${results.email_enabled ? 'enabled' : 'disabled'}">
              ${results.email_enabled ? '有効' : '無効'}
            </div>
          </div>
          <div class="status-item">
            <h5>Slack通知</h5>
            <div class="status-value ${results.slack_enabled ? 'enabled' : 'disabled'}">
              ${results.slack_enabled ? '有効' : '無効'}
            </div>
          </div>
          <div class="status-item">
            <h5>SMTP設定</h5>
            <div class="status-value ${results.smtp_configured ? 'configured' : 'not-configured'}">
              ${results.smtp_configured ? '設定済み' : '未設定'}
            </div>
          </div>
          <div class="status-item">
            <h5>Slack設定</h5>
            <div class="status-value ${results.slack_configured ? 'configured' : 'not-configured'}">
              ${results.slack_configured ? '設定済み' : '未設定'}
            </div>
          </div>
        `;
      }
    }
    
  } catch (error) {
    console.error('Error updating notification status:', error);
  }
}

// 通知を表示
function showNotification(message, type = 'info') {
  // 既存の通知を削除
  const existingNotification = document.querySelector('.notification-toast');
  if (existingNotification) {
    existingNotification.remove();
  }
  
  // 新しい通知を作成
  const notification = document.createElement('div');
  notification.className = `notification-toast ${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
      <span>${message}</span>
      <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  
  // 通知を追加
  document.body.appendChild(notification);
  
  // 自動削除
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 5000);
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initMobileMenu();
  initTouchOptimization();
  initResponsiveHandling();
  initSearchForm();
  initClassifyForm();
  initMonitoring();
  initAnalytics();
  initAssistant();
  initReports();
  initNotifications();
  initServiceWorker();
  
  console.log('PRISM v2.0.0 Web UI initialized with mobile support, AI assistant, reports, and notifications');
});