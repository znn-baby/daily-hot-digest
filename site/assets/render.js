/**
 * Daily Hot Digest — Client-side Render Engine
 * 将 JSON 数据渲染为卡片 HTML（端口自 Python generator）
 */

var DigestRender = (function() {
    'use strict';

    var SOURCE_COLOR_MAP = {
        'GitHub': 'dev', 'GitHub Trending': 'dev',
        'Lobsters': 'sys',
        '少数派': 'gadget',
        '微博': 'opinion', '微博热搜': 'opinion',
        '知乎': 'opinion', '知乎热榜': 'opinion',
        'Hacker News': 'dev'
    };

    var WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

    // ── Utilities ──

    function esc(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function colorOf(source) {
        for (var key in SOURCE_COLOR_MAP) {
            if (source.indexOf(key) !== -1) return SOURCE_COLOR_MAP[key];
        }
        return 'opinion';
    }

    function fmtNum(n) {
        if (n === undefined || n === null) return '';
        return Number(n).toLocaleString('en-US');
    }

    function fmtDate(dateStr) {
        var p = dateStr.split('-');
        var d = new Date(parseInt(p[0]), parseInt(p[1]) - 1, parseInt(p[2]));
        return p[0] + ' 年 ' + d.getMonth() + ' 月 ' + d.getDate() + ' 日 · ' + WEEKDAYS[d.getDay()];
    }

    // ── Source Card Builders ──
    // 每个函数返回 { html, items }，items 用于溯源索引

    function buildGitHub(data, startNum) {
        var items = data.github_trending || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], tags = '';

        items.forEach(function(item) {
            num++;
            var title = esc(item.title.replace(' / ', '/'));
            var repo = title.split(' - ')[0].split(' / ')[0];
            var stars = item.stars ? fmtNum(item.stars) : '';
            var starsSpan = '<span class="gh-stars" data-repo="' + repo + '">' + (stars || '—') + '</span>';
            tags += '<a class="gh-item" href="' + esc(item.url) + '" target="_blank">' +
                    title + starsSpan + '</a>\n';
            sources.push({ num: num, title: title, url: item.url,
                source: 'GitHub Trending', desc: item.description || '' });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-dev"></span>' +
            '<span class="title"><span class="highlight-dev">GitHub</span> Trending</span>' +
            '<span class="count-badge">' + items.length + ' repos</span></div>' +
            '<p>' + tags + '</p></div>';
        return { html: html, items: sources, nextNum: num };
    }

    function buildLobsters(data, startNum) {
        var items = data.lobsters || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], list = '';

        items.forEach(function(item) {
            num++;
            var tags = (item.tags || []).map(function(t) {
                return '<span style="background:rgba(0,0,0,0.04);padding:0 8px;' +
                    'border-radius:4px;font-size:12px;color:var(--text-muted);">' + esc(t) + '</span>';
            }).join(' ');
            list += '<li style="margin-bottom:6px;"><a href="' + esc(item.url) +
                '" target="_blank" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">' +
                esc(item.title) + '</a> ' + tags + '</li>\n';
            sources.push({ num: num, title: item.title, url: item.url,
                source: 'Lobsters', desc: (item.tags || []).join(', ') });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-sys"></span>' +
            '<span class="title"><span class="highlight-sys">Lobsters</span> 热帖</span>' +
            '<span class="count-badge">' + items.length + ' topics</span></div>' +
            '<ul style="list-style:none;padding:0;">' + list + '</ul></div>';
        return { html: html, items: sources, nextNum: num };
    }

    function buildSspai(data, startNum) {
        var items = data.sspai || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], list = '';

        items.forEach(function(item) {
            num++;
            var author = item.author
                ? ' <span style="color:var(--text-muted);font-size:12px;">(' + esc(item.author) + ')</span>'
                : '';
            list += '<li style="margin-bottom:6px;"><a href="' + esc(item.url) +
                '" target="_blank" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">' +
                esc(item.title) + '</a>' + author + '</li>\n';
            sources.push({ num: num, title: item.title, url: item.url,
                source: '少数派', desc: item.author || '' });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-gadget"></span>' +
            '<span class="title"><span class="highlight-gadget">少数派</span>精选</span>' +
            '<span class="count-badge">' + items.length + ' articles</span></div>' +
            '<ul style="list-style:none;padding:0;">' + list + '</ul></div>';
        return { html: html, items: sources, nextNum: num };
    }

    function buildWeibo(data, startNum) {
        var items = data.weibo || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], list = '';

        items.forEach(function(item) {
            num++;
            var label = item.label
                ? ' <span style="background:#ff8200;color:#fff;padding:0 6px;border-radius:3px;font-size:11px;font-weight:600;">' + esc(item.label) + '</span>'
                : '';
            var hot = item.hot_value ? ' <span style="color:var(--text-muted);font-size:12px;">' + fmtNum(item.hot_value) + '</span>' : '';
            list += '<li style="margin-bottom:6px;"><a href="' + esc(item.url) +
                '" target="_blank" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">' +
                esc(item.title) + '</a>' + label + hot + '</li>\n';
            sources.push({ num: num, title: item.title, url: item.url,
                source: '微博热搜',
                desc: item.hot_value ? '热度 ' + fmtNum(item.hot_value) : '' });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-opinion"></span>' +
            '<span class="title"><span class="highlight-opinion">微博</span>热搜</span>' +
            '<span class="count-badge">' + items.length + ' topics</span></div>' +
            '<ul style="list-style:none;padding:0;">' + list + '</ul></div>';
        return { html: html, items: sources, nextNum: num };
    }

    function buildZhihu(data, startNum) {
        var items = data.zhihu || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], list = '';

        items.forEach(function(item) {
            num++;
            var excerpt = item.excerpt
                ? '<div style="font-size:12px;color:var(--text-muted);margin-top:2px;">' + esc(item.excerpt) + '</div>'
                : '';
            list += '<li style="margin-bottom:8px;"><a href="' + esc(item.url) +
                '" target="_blank" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">' +
                esc(item.title) + '</a>' + excerpt + '</li>\n';
            sources.push({ num: num, title: item.title, url: item.url,
                source: '知乎热榜', desc: item.hot_value || '' });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-opinion"></span>' +
            '<span class="title"><span class="highlight-opinion">知乎</span>热榜</span>' +
            '<span class="count-badge">' + items.length + ' topics</span></div>' +
            '<ul style="list-style:none;padding:0;">' + list + '</ul></div>';
        return { html: html, items: sources, nextNum: num };
    }

    function buildHN(data, startNum) {
        var items = data.hackernews || [];
        if (!items.length) return { html: '', items: [] };
        var num = startNum, sources = [], list = '';

        items.forEach(function(item) {
            num++;
            var score = item.score || 0, comments = item.comments || 0;
            var meta = ' <span style="color:var(--text-muted);font-size:12px;">' +
                score + ' pts · ' + comments + ' comments</span>';
            list += '<li style="margin-bottom:6px;"><a href="' + esc(item.url) +
                '" target="_blank" style="color:var(--text-secondary);text-decoration:none;font-weight:500;">' +
                esc(item.title) + '</a>' + meta + '</li>\n';
            sources.push({ num: num, title: item.title, url: item.url,
                source: 'Hacker News', desc: score + ' pts' });
        });

        var html = '<div class="card"><div class="card-header">' +
            '<span class="dot dot-dev"></span>' +
            '<span class="title"><span class="highlight-dev">Hacker</span> News</span>' +
            '<span class="count-badge">' + items.length + ' stories</span></div>' +
            '<ul style="list-style:none;padding:0;">' + list + '</ul></div>';
        return { html: html, items: sources, nextNum: num };
    }

    // ── Composite Builders ──

    function buildRawDataCards(data) {
        var n = 0, allSources = [], html = '';
        var builders = [buildGitHub, buildLobsters, buildSspai, buildWeibo, buildZhihu, buildHN];

        builders.forEach(function(build) {
            var result = build(data, n);
            if (result.html) {
                html += result.html;
                allSources = allSources.concat(result.items);
                n = result.nextNum;
            }
        });

        return { html: html, sources: allSources };
    }

    function buildAiCards(aiSummary) {
        var categories = aiSummary.categories || [];
        var sources = aiSummary.sources || [];
        var html = '';

        categories.forEach(function(cat) {
            var colorKey = cat.color || 'ai';
            var name = esc(cat.name || '未分类');
            var summary = cat.summary || '';

            // [N] / [vN] → superscript link
            var summaryHtml = summary.replace(/\[v?(\d+)\]/g, function(m, num) {
                return '<span class="cite"><a href="#src' + num + '">[' + num + ']</a></span>';
            });

            // Auto-split at source transitions
            summaryHtml = summaryHtml
                .replace(/(?=Lobsters)/g, '\n')
                .replace(/(?=少数派)/g, '\n')
                .replace(/(?=社区\s*(?:今天|上|里|的))/g, '\n');
            summaryHtml = summaryHtml.replace(/\n{2,}/g, '\n').trim();

            var paragraphs = summaryHtml.split('\n')
                .filter(function(p) { return p.trim(); })
                .map(function(p) { return '<p>' + p.trim() + '</p>'; })
                .join('');

            html += '<div class="card"><div class="card-header">' +
                '<span class="dot dot-' + colorKey + '"></span>' +
                '<span class="title"><span class="highlight-' + colorKey + '">' + name + '</span></span>' +
                '</div>' + paragraphs + '</div>';
        });

        return { html: html, sources: sources };
    }

    function buildSourceIndex(sources) {
        var groups = {};
        sources.forEach(function(src) {
            if (!groups[src.source]) groups[src.source] = [];
            groups[src.source].push(src);
        });

        var html = '';
        for (var sourceName in groups) {
            var ck = colorOf(sourceName);
            html += '<div class="source-group">' +
                '<div class="source-group-title">' + esc(sourceName) + '</div>' +
                '<ul class="source-list">';
            groups[sourceName].forEach(function(item) {
                html += '<li id="src' + item.num + '">' +
                    '<span class="num num-' + ck + '">' + item.num + '</span>' +
                    '<a href="' + esc(item.url) + '" target="_blank">' + esc(item.title) + '</a> ' +
                    '<span class="desc">— ' + esc(item.desc) + '</span></li>';
            });
            html += '</ul></div>';
        }
        return html;
    }

    // ── Public API ──

    return {
        buildRawDataCards: buildRawDataCards,
        buildAiCards: buildAiCards,
        buildSourceIndex: buildSourceIndex,
        fmtDate: fmtDate,
        fmtNum: fmtNum,
        esc: esc
    };
})();
