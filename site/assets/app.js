/**
 * Daily Hot Digest — Main App
 * 路由 / 数据加载 / 页面渲染 / 归档视图
 */
(function() {
    'use strict';

    var DATA_BASE = 'data/';
    var indexData = null;   // { dates: ['2026-07-30', ...] }
    var currentDate = null;

    // ── Init ──

    function init() {
        window.addEventListener('hashchange', onHashChange);
        loadIndex().then(function() {
            renderCurrentRoute();
        }).catch(function(err) {
            console.error('Failed to load index:', err);
            showError('无法加载归档索引');
        });
    }

    function onHashChange() {
        renderCurrentRoute();
    }

    function renderCurrentRoute() {
        var hash = location.hash.replace('#/', '').replace('#', '');
        if (hash === 'archive' || hash === '') {
            if (indexData && indexData.dates && indexData.dates.length > 0) {
                if (hash === 'archive') {
                    renderArchive();
                } else {
                    loadDate(indexData.dates[0]);
                }
            } else {
                showEmpty();
            }
        } else if (/^\d{4}-\d{2}-\d{2}$/.test(hash)) {
            loadDate(hash);
        } else {
            loadDate(indexData.dates[0]);
        }
    }

    // ── Data Fetching ──

    function loadIndex() {
        return fetch(DATA_BASE + 'index.json', { cache: 'no-cache' })
            .then(function(res) {
                if (!res.ok) throw new Error('index.json not found');
                return res.json();
            })
            .then(function(data) {
                indexData = data;
            });
    }

    function loadDate(dateStr) {
        currentDate = dateStr;
        var content = document.getElementById('content');
        content.innerHTML = '<div class="loading">加载中...</div>';

        fetch(DATA_BASE + dateStr + '.json')
            .then(function(res) {
                if (!res.ok) throw new Error('Data not found: ' + dateStr);
                return res.json();
            })
            .then(function(data) {
                renderPage(dateStr, data);
            })
            .catch(function(err) {
                console.error(err);
                showError('无法加载 ' + dateStr + ' 的数据');
            });
    }

    // ── Page Rendering ──

    function renderPage(dateStr, data) {
        var R = DigestRender;
        var aiSummary = data.ai_summary || null;
        var content = document.getElementById('content');
        var hasAi = !!aiSummary;

        // Title
        document.title = 'Daily Hot Digest | ' + dateStr;

        // Build raw data cards + sources
        var raw = R.buildRawDataCards(data);
        var rawHtml = raw.html;
        var rawSources = raw.sources;

        // Build AI cards + sources
        var aiHtml = '', aiSources = [];
        if (hasAi) {
            var ai = R.buildAiCards(aiSummary);
            aiHtml = ai.html;
            aiSources = ai.sources;
        }

        // Stats
        var sourceCount, categoryCount, itemCount;
        if (hasAi) {
            var sourcesBySource = {};
            aiSources.forEach(function(s) { sourcesBySource[s.source] = true; });
            sourceCount = Object.keys(sourcesBySource).length;
            categoryCount = (aiSummary.categories || []).length;
            itemCount = (aiSummary.stats && aiSummary.stats.total_items) || aiSources.length;
        } else {
            var dataSources = {};
            rawSources.forEach(function(s) { dataSources[s.source] = true; });
            sourceCount = Object.keys(dataSources).length;
            var sourceKeys = ['github_trending', 'lobsters', 'sspai', 'weibo', 'zhihu', 'hackernews'];
            categoryCount = sourceKeys.filter(function(k) { return data[k] && data[k].length > 0; }).length;
            itemCount = rawSources.length;
        }

        // Source index
        var indexSources = hasAi ? aiSources : rawSources;
        var indexHtml = R.buildSourceIndex(indexSources);

        // Tab buttons
        var tabsHtml = '';
        if (hasAi) {
            tabsHtml = '<div class="view-tabs">' +
                '<div class="view-tab active" data-view="ai">AI 简报</div>' +
                '<div class="view-tab" data-view="raw">信息源</div></div>';
        }

        // Nav
        var navHtml = buildNav(dateStr);

        // Assemble
        content.innerHTML =
            '<header class="header">' +
                '<div class="header-badge">&#10022; 晴空 &middot; 每日信号</div>' +
                '<h1>Daily Hot Digest</h1>' +
                '<div class="sub">' + R.fmtDate(dateStr) +
                    ' &nbsp;&middot;&nbsp; <em>' + itemCount + ' 条内容</em></div>' +
                '<div class="stats-row">' +
                    '<span class="stat-item"><span class="num" data-target="' + sourceCount + '">0</span><span class="label">信息源</span></span>' +
                    '<span class="stat-item"><span class="num" data-target="' + categoryCount + '">0</span><span class="label">分类</span></span>' +
                    '<span class="stat-item"><span class="num" data-target="' + itemCount + '">0</span><span class="label">条目</span></span>' +
                '</div>' +
                navHtml +
            '</header>' +
            tabsHtml +
            '<div id="view-ai" style="' + (hasAi ? '' : 'display:none;') + '">' + aiHtml + '</div>' +
            '<div id="view-raw" style="' + (hasAi ? 'display:none;' : '') + '">' + rawHtml + '</div>' +
            '<div class="source-index" id="source-index" style="' + (hasAi ? '' : 'display:none;') + '">' +
                '<h2>&#9114; 溯源索引</h2>' + indexHtml +
            '</div>' +
            '<footer class="footer">' +
                '<span class="heart">&#10022;</span> Daily Hot Digest &middot; 数据截至 ' + dateStr +
            '</footer>';

        // Post-render: init tabs, counters, stars
        if (hasAi) initTabs();
        document.dispatchEvent(new CustomEvent('digest:rendered'));
    }

    function buildNav(dateStr) {
        if (!indexData || !indexData.dates) return '';
        var dates = indexData.dates;
        var idx = dates.indexOf(dateStr);
        var prev = idx < dates.length - 1 ? dates[idx + 1] : null;  // older
        var next = idx > 0 ? dates[idx - 1] : null;                  // newer

        var links = '<a class="nav-link" href="#/archive">&larr; 归档</a>';
        if (next) links += ' <a class="nav-link" href="#/' + next + '">&larr; 前一天</a>';
        if (prev) links += ' <a class="nav-link" href="#/' + prev + '">后一天 &rarr;</a>';
        return '<div class="page-nav">' + links + '</div>';
    }

    // ── Archive View ──

    function renderArchive() {
        document.title = 'Daily Hot Digest - Archive';
        var content = document.getElementById('content');
        var dates = indexData.dates;

        // Group by year → month
        var grouped = {};
        dates.forEach(function(d) {
            var p = d.split('-');
            var y = parseInt(p[0]), m = parseInt(p[1]);
            if (!grouped[y]) grouped[y] = {};
            if (!grouped[y][m]) grouped[y][m] = [];
            grouped[y][m].push(d);
        });

        var MONTH_NAMES = ['', '一月', '二月', '三月', '四月', '五月', '六月',
            '七月', '八月', '九月', '十月', '十一月', '十二月'];
        var WD = ['日', '一', '二', '三', '四', '五', '六'];

        var html = '<div class="index-header">' +
            '<h1>Daily Hot Digest</h1>' +
            '<p>自动抓取 GitHub / Lobsters / 少数派 / 微博 / 知乎 / Hacker News + AI 摘要</p></div>';

        var years = Object.keys(grouped).sort(function(a, b) { return b - a; });
        years.forEach(function(year) {
            html += '<h2 class="archive-year">' + year + '</h2>';
            var months = Object.keys(grouped[year]).sort(function(a, b) { return b - a; });
            months.forEach(function(month) {
                var monthDates = grouped[year][month].sort().reverse();
                var tags = monthDates.map(function(d) {
                    var day = parseInt(d.split('-')[2]);
                    var dt = new Date(parseInt(d.split('-')[0]), parseInt(d.split('-')[1]) - 1, day);
                    return '<li><a href="#/' + d + '">' + day + '日 周' + WD[dt.getDay()] + '</a></li>';
                }).join('');

                html += '<div class="archive-month">' +
                    '<div class="archive-month-header">' +
                        '<span class="month-title">' + MONTH_NAMES[parseInt(month)] + '</span>' +
                        '<span class="month-count">' + monthDates.length + ' 期</span>' +
                    '</div>' +
                    '<ul class="archive-dates">' + tags + '</ul></div>';
            });
        });

        html += '<footer class="footer">Powered by GitHub Actions &middot; 每日 22:00 自动更新</footer>';
        content.innerHTML = html;
    }

    // ── Helpers ──

    function initTabs() {
        var tabs = document.querySelectorAll('.view-tab');
        var sourceIndex = document.getElementById('source-index');
        tabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                var target = this.dataset.view;
                tabs.forEach(function(t) { t.classList.remove('active'); });
                this.classList.add('active');
                document.getElementById('view-ai').style.display = target === 'ai' ? '' : 'none';
                document.getElementById('view-raw').style.display = target === 'raw' ? '' : 'none';
                if (sourceIndex) sourceIndex.style.display = target === 'ai' ? '' : 'none';
            });
        });
    }

    function showError(msg) {
        document.getElementById('content').innerHTML =
            '<div class="empty">' + DigestRender.esc(msg) +
            '<br><br><a href="#/archive">查看归档</a></div>';
    }

    function showEmpty() {
        document.getElementById('content').innerHTML =
            '<div class="empty">暂无内容，等待首次自动生成...</div>';
    }

    // ── Start ──

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
