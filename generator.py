"""HTML 生成模块 - 数据宇宙主题 · 带溯源索引的静态页面"""

import os
import re
import json
from string import Template
from datetime import datetime

# 分类颜色映射（深色主题高饱和度色板）
COLORS = {
    "ai":       ("#f97316", "AI / 智能体"),
    "dev":      ("#3b82f6", "开发工具 / 工程实践"),
    "sys":      ("#22c55e", "系统与底层技术"),
    "gadget":   ("#a855f7", "数码产品 / 效率工具"),
    "opinion":  ("#eab308", "思考与观点"),
    "security": ("#ef4444", "安全"),
    "web":      ("#06b6d4", "Web 开发"),
}

# 来源名称 -> 颜色 key 映射
SOURCE_COLOR_MAP = {
    "GitHub": "dev",
    "GitHub Trending": "dev",
    "Lobsters": "sys",
    "少数派": "gadget",
    "微博": "opinion",
    "微博热搜": "opinion",
    "知乎": "opinion",
    "知乎热榜": "opinion",
    "Hacker News": "dev",
}


def _get_color(color_key: str) -> str:
    """获取分类颜色值"""
    return COLORS.get(color_key, ("#888", color_key))[0]


def _get_color_name(color_key: str) -> str:
    """获取分类中文名"""
    return COLORS.get(color_key, ("#888", color_key))[1]


def _generate_color_classes() -> str:
    """根据 COLORS 字典生成动态 CSS 规则（使用 CSS 变量）"""
    rules = []
    for key, (_, _) in COLORS.items():
        rules.append(f".dot-{key} {{ background: var(--color-{key}); }}")
        rules.append(f".num-{key} {{ background: var(--color-{key}); }}")
        rules.append(f".highlight-{key} {{ color: var(--color-{key}); }}")
    return "\n".join(rules)


def _render_template(template_str: str, **kwargs) -> str:
    """使用 string.Template 渲染，避免 .format() 的花括号转义问题"""
    return Template(template_str).safe_substitute(**kwargs)


# ============================================================
# JavaScript 常量（作为独立字符串，便于维护）
# ============================================================

PARTICLE_JS = r"""
(function() {
    'use strict';
    var canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W, H;

    function resize() {
        W = window.innerWidth; H = window.innerHeight;
        canvas.width = W; canvas.height = H;
    }
    window.addEventListener('resize', resize);
    resize();

    // 加载蓝天白云背景图片
    var bgImage = new Image();
    bgImage.crossOrigin = 'anonymous';
    bgImage.src = 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80';
    var bgLoaded = false;
    bgImage.onload = function() { bgLoaded = true; };
    bgImage.onerror = function() { bgLoaded = false; };

    // 粒子系统（适配蓝天白云风格）
    var particles = [];
    var PARTICLE_COUNT = 100;
    var CONNECTION_DIST = 130;
    var MOUSE_RADIUS = 160;
    var mouseX = null, mouseY = null;

    var colorPalette = [
        'hsla(210, 80%, 90%, 0.7)',
        'hsla(200, 70%, 85%, 0.6)',
        'hsla(40, 60%, 92%, 0.5)',
        'hsla(0, 50%, 95%, 0.5)',
        'hsla(190, 60%, 88%, 0.6)',
        'hsla(220, 50%, 92%, 0.6)',
    ];

    function Particle() { this.reset(); }
    Particle.prototype.reset = function() {
        this.x = Math.random() * W; this.y = Math.random() * H;
        this.vx = (Math.random() - 0.5) * 0.6; this.vy = (Math.random() - 0.5) * 0.6;
        this.radius = 2 + Math.random() * 3;
        this.color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
    };
    Particle.prototype.update = function() {
        this.x += this.vx; this.y += this.vy;
        if (mouseX !== null && mouseY !== null) {
            var dx = this.x - mouseX, dy = this.y - mouseY;
            var dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < MOUSE_RADIUS && dist > 1) {
                var force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS * 0.4;
                this.x += (dx / dist) * force; this.y += (dy / dist) * force;
            }
        }
        if (this.x < 0) { this.x = 0; this.vx *= -0.5; }
        if (this.x > W) { this.x = W; this.vx *= -0.5; }
        if (this.y < 0) { this.y = 0; this.vy *= -0.5; }
        if (this.y > H) { this.y = H; this.vy *= -0.5; }
        this.vx += (Math.random() - 0.5) * 0.03;
        this.vy += (Math.random() - 0.5) * 0.03;
        var sp = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        if (sp > 0.8) { this.vx = (this.vx / sp) * 0.8; this.vy = (this.vy / sp) * 0.8; }
    };
    Particle.prototype.draw = function() {
        ctx.beginPath(); ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.shadowColor = 'rgba(255,255,255,0.3)'; ctx.shadowBlur = 10;
        ctx.fill(); ctx.shadowBlur = 0;
    };

    for (var i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());

    function drawConnections() {
        for (var i = 0; i < particles.length; i++) {
            for (var j = i + 1; j < particles.length; j++) {
                var dx = particles[i].x - particles[j].x;
                var dy = particles[i].y - particles[j].y;
                var dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < CONNECTION_DIST) {
                    var alpha = (1 - dist / CONNECTION_DIST) * 0.2;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(255, 255, 255, ' + alpha + ')';
                    ctx.lineWidth = 0.8; ctx.stroke();
                }
            }
        }
    }

    document.addEventListener('mousemove', function(e) { mouseX = e.clientX; mouseY = e.clientY; });
    document.addEventListener('mouseleave', function() { mouseX = null; mouseY = null; });
    document.addEventListener('touchmove', function(e) {
        var t = e.touches[0]; if (t) { mouseX = t.clientX; mouseY = t.clientY; }
    }, { passive: true });
    document.addEventListener('touchend', function() { mouseX = null; mouseY = null; });

    function render() {
        ctx.clearRect(0, 0, W, H);
        if (bgLoaded && bgImage.complete && bgImage.naturalWidth > 0) {
            var imgAspect = bgImage.naturalWidth / bgImage.naturalHeight;
            var canvasAspect = W / H;
            var drawW, drawH, offsetX, offsetY;
            if (imgAspect > canvasAspect) {
                drawW = W; drawH = W / imgAspect; offsetX = 0; offsetY = (H - drawH) / 2;
            } else {
                drawH = H; drawW = H * imgAspect; offsetX = (W - drawW) / 2; offsetY = 0;
            }
            ctx.drawImage(bgImage, offsetX, offsetY, drawW, drawH);
        } else {
            var grad = ctx.createLinearGradient(0, 0, 0, H);
            grad.addColorStop(0, '#87CEEB'); grad.addColorStop(1, '#E0F0FF');
            ctx.fillStyle = grad; ctx.fillRect(0, 0, W, H);
        }
        drawConnections();
        for (var i = 0; i < particles.length; i++) { particles[i].update(); particles[i].draw(); }
        requestAnimationFrame(render);
    }

    resize(); render();
    window.addEventListener('resize', function() {
        resize();
        for (var i = 0; i < particles.length; i++) {
            particles[i].x = Math.min(particles[i].x, W);
            particles[i].y = Math.min(particles[i].y, H);
        }
    });
})();
"""

COUNTER_JS = r"""
(function() {
    'use strict';

    // 统计数字动画
    function animateNumber(el, target, duration) {
        duration = duration || 1200;
        var startTime = performance.now();
        function update(currentTime) {
            var elapsed = currentTime - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 4);
            el.textContent = Math.round(target * eased);
            if (progress < 1) requestAnimationFrame(update);
            else el.textContent = target;
        }
        requestAnimationFrame(update);
    }
    var statsItems = document.querySelectorAll('.stat-item .num[data-target]');
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                var target = parseInt(entry.target.dataset.target, 10);
                if (!isNaN(target)) animateNumber(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });
    statsItems.forEach(function(el) { observer.observe(el); });

    // GitHub Stars 获取
    var starElements = document.querySelectorAll('.gh-stars[data-repo]');
    if (starElements.length > 0) {
        setTimeout(function() {
            starElements.forEach(function(el) {
                var repo = el.dataset.repo;
                if (!repo) return;
                fetch('https://api.github.com/repos/' + repo, {
                    headers: { 'Accept': 'application/vnd.github.v3+json' }
                }).then(function(res) {
                    if (!res.ok) return;
                    return res.json();
                }).then(function(data) {
                    if (data && data.stargazers_count !== undefined) {
                        el.textContent = data.stargazers_count.toLocaleString();
                    }
                }).catch(function() {});
            });
        }, 800);
    }
})();
"""


# ============================================================
# HTML 模板 — 数据宇宙主题
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Hot Digest | $date</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
    --bg-primary: #f0f4fa;
    --bg-card: rgba(255, 255, 255, 0.55);
    --border-card: rgba(255, 255, 255, 0.25);
    --text-primary: #1e293b;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --shadow-card: 0 12px 40px rgba(0, 0, 0, 0.08);
    --radius-card: 20px;
    --transition-smooth: cubic-bezier(0.22, 1, 0.36, 1);
    --color-ai: #f97316;
    --color-dev: #3b82f6;
    --color-sys: #22c55e;
    --color-gadget: #a855f7;
    --color-opinion: #eab308;
}
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', -apple-system, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    background: var(--bg-primary); color: var(--text-primary);
    min-height: 100vh; overflow-x: hidden; line-height: 1.7;
}
#bg-canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; pointer-events: none; }
.container { position: relative; z-index: 2; max-width: 820px; margin: 0 auto; padding: 48px 24px 64px; }
.header { text-align: center; padding: 24px 0 48px; }
.header-badge {
    display: inline-block; background: rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.4);
    padding: 6px 18px; border-radius: 100px; font-size: 12px;
    font-weight: 600; letter-spacing: 0.5px; color: var(--text-secondary); margin-bottom: 20px; text-transform: uppercase;
}
.header h1 {
    font-size: clamp(40px, 8vw, 68px); font-weight: 800; letter-spacing: -0.03em; line-height: 1.05;
    color: var(--text-primary);
    text-shadow: 0 2px 20px rgba(255, 255, 255, 0.5); margin-bottom: 12px;
}
.header .sub { font-size: 16px; color: var(--text-secondary); font-weight: 400; letter-spacing: 1px; }
.header .sub em { font-style: normal; color: var(--text-primary); font-weight: 500; }
.stats-row { display: flex; justify-content: center; gap: 12px 24px; flex-wrap: wrap; margin-top: 28px; }
.stats-row .stat-item {
    background: rgba(255, 255, 255, 0.3); border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(8px); padding: 8px 22px; border-radius: 100px; font-size: 13px;
    color: var(--text-secondary); display: flex; align-items: center; gap: 8px;
}
.stats-row .stat-item .num { font-weight: 700; font-size: 16px; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.stats-row .stat-item .label { font-weight: 400; }
.nav-link {
    display: inline-block; margin-top: 16px; font-size: 13px;
    color: var(--text-muted); text-decoration: none;
    border-bottom: 1px dashed rgba(255,255,255,0.1);
}
.nav-link:hover { color: var(--text-secondary); }

/* === 卡片 === */
.card {
    background: var(--bg-card); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-card); border-radius: var(--radius-card);
    padding: 28px 32px; margin-bottom: 20px; box-shadow: var(--shadow-card);
    transition: transform 0.4s var(--transition-smooth), box-shadow 0.4s var(--transition-smooth), border-color 0.3s ease;
    opacity: 0; transform: translateY(30px); animation: cardEnter 0.7s var(--transition-smooth) forwards;
}
.card:hover { transform: translateY(-4px); box-shadow: 0 20px 48px rgba(0, 0, 0, 0.12); border-color: rgba(255, 255, 255, 0.5); }
@keyframes cardEnter { to { opacity: 1; transform: translateY(0); } }
.card:nth-child(1) { animation-delay: 0.05s; }
.card:nth-child(2) { animation-delay: 0.12s; }
.card:nth-child(3) { animation-delay: 0.19s; }
.card:nth-child(4) { animation-delay: 0.26s; }
.card:nth-child(5) { animation-delay: 0.33s; }
.card:nth-child(6) { animation-delay: 0.40s; }
.card:nth-child(7) { animation-delay: 0.47s; }
.card-header {
    display: flex; align-items: center; gap: 14px; margin-bottom: 18px;
    padding-bottom: 14px; border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.card-header .dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.card-header .title { font-size: 20px; font-weight: 700; letter-spacing: -0.01em; }
.card-header .count-badge {
    margin-left: auto; font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; color: var(--text-muted); background: rgba(0, 0, 0, 0.04);
    padding: 2px 14px; border-radius: 100px; border: 1px solid rgba(0, 0, 0, 0.04);
}
.card p { font-size: 15px; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.8; }
.card p:last-child { margin-bottom: 0; }
.card p .highlight { color: var(--text-primary); font-weight: 500; }

/* === 内联项目标签 === */
.gh-item {
    display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.06); padding: 1px 12px 1px 8px; border-radius: 100px;
    font-size: 13px; font-weight: 500; color: var(--text-primary); white-space: nowrap;
    transition: background 0.2s, border-color 0.2s; margin: 0 2px; text-decoration: none;
}
.gh-item:hover { background: rgba(0, 0, 0, 0.08); border-color: rgba(0, 0, 0, 0.12); }
.gh-item .gh-stars { font-weight: 600; color: var(--color-opinion); font-size: 12px; margin-left: 2px; }
.gh-item .gh-stars::before { content: '\\2605 '; font-weight: 400; }

/* === 引用上标 === */
.cite { display: inline; font-size: 11px; font-weight: 700; vertical-align: super; line-height: 1; padding: 0 2px; }
.cite a { text-decoration: none; color: var(--text-muted); transition: color 0.2s; }
.cite a:hover { color: var(--text-primary); }

/* === 结构化新闻条目 === */
.card-intro {
    font-size: 14px; color: var(--text-muted); font-style: italic;
    margin-bottom: 16px; padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.news-item {
    padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.news-item:last-child { border-bottom: none; padding-bottom: 0; }
.news-item:first-of-type { padding-top: 4px; }
.news-item-title {
    font-size: 15px; font-weight: 600; color: var(--text-primary);
    margin-bottom: 4px; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;
}
.news-item-title .item-name { font-weight: 700; }
.news-item-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.7; margin-bottom: 4px; }
.news-item-note {
    font-size: 13px; color: var(--text-muted); font-style: italic;
    padding-left: 12px; border-left: 2px solid rgba(255,255,255,0.08);
    margin-top: 4px;
}
.news-item-cites { display: inline-flex; gap: 4px; margin-left: auto; }
.news-item-cites .cite a {
    background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 4px;
    font-size: 10px; font-weight: 600;
}
.news-item-cites .cite a:hover { background: rgba(255,255,255,0.12); color: var(--text-primary); }

/* === 溯源索引 === */
.source-index {
    background: var(--bg-card); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-card); border-radius: var(--radius-card);
    padding: 28px 32px; margin-top: 32px; box-shadow: var(--shadow-card);
    opacity: 0; transform: translateY(30px); animation: cardEnter 0.7s var(--transition-smooth) 0.4s forwards;
}
.source-index h2 {
    font-size: 18px; font-weight: 700; margin-bottom: 24px;
    padding-bottom: 14px; border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    letter-spacing: -0.01em; color: var(--text-primary);
}
.source-group { margin-bottom: 24px; }
.source-group:last-child { margin-bottom: 0; }
.source-group-title {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1.2px; color: var(--text-muted); margin-bottom: 10px;
}
.source-list { list-style: none; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px 16px; }
@media (max-width: 600px) { .source-list { grid-template-columns: 1fr; } }
.source-list li {
    font-size: 14px; padding: 6px 0; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.03);
}
.source-list li .num {
    flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%; font-size: 10px; font-weight: 700;
    color: #fff; background: rgba(0, 0, 0, 0.2);
}
.source-list li a { color: var(--text-secondary); text-decoration: none; transition: color 0.2s; font-weight: 500; font-size: 13px; }
.source-list li a:hover { color: var(--text-primary); }
.source-list li .desc { color: var(--text-muted); font-size: 12px; font-weight: 400; }

/* === Footer === */
.footer {
    text-align: center; margin-top: 40px; font-size: 12px; color: var(--text-muted);
    letter-spacing: 0.3px; border-top: 1px solid rgba(0, 0, 0, 0.05); padding-top: 28px;
}
.footer a { color: var(--text-muted); text-decoration: none; }
.footer a:hover { color: var(--text-secondary); }
.footer .heart { color: var(--color-ai); display: inline-block; animation: heartBeat 2s ease-in-out infinite; }
@keyframes heartBeat { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.2); } }

/* === 动态颜色类 === */
$color_classes

/* === 响应式 === */
@media (max-width: 640px) {
    .container { padding: 24px 16px 40px; }
    .card { padding: 20px 18px; border-radius: 16px; }
    .source-index { padding: 20px 18px; }
    .card-header .title { font-size: 17px; }
    .card p { font-size: 14px; }
    .stats-row .stat-item { padding: 6px 14px; font-size: 12px; }
    .gh-item { font-size: 12px; padding: 1px 10px 1px 6px; }
    .header h1 { font-size: 32px; }
    .source-list li a { font-size: 12px; }
}

/* === 滚动条 === */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.15); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 0, 0, 0.25); }

/* === 触摸设备 === */
@media (hover: none) {
    .card:hover { transform: none; box-shadow: var(--shadow-card); }
    .gh-item:hover { background: rgba(0, 0, 0, 0.04); border-color: rgba(0, 0, 0, 0.06); }
}
</style>
</head>
<body>
<canvas id="bg-canvas"></canvas>
<div class="container">
    <header class="header">
        <div class="header-badge">&#10022; 晴空 &middot; 每日信号</div>
        <h1>Daily Hot Digest</h1>
        <div class="sub">$date_display &nbsp;&middot;&nbsp; <em>$item_count 条内容</em></div>
        <div class="stats-row">
            <span class="stat-item"><span class="num" data-target="$source_count">0</span><span class="label">信息源</span></span>
            <span class="stat-item"><span class="num" data-target="$category_count">0</span><span class="label">分类</span></span>
            <span class="stat-item"><span class="num" data-target="$item_count">0</span><span class="label">条目</span></span>
        </div>
        <a class="nav-link" href="index.html">&larr; 查看所有日期</a>
    </header>

$categories_html

    <div class="source-index" id="source-index">
        <h2>&#9114; 溯源索引</h2>
$sources_by_group_html
    </div>

    <footer class="footer">
        <span class="heart">&#10022;</span> Daily Hot Digest &middot; 数据截至 $date &middot;
        <a href="index.html">查看所有日期</a>
    </footer>
</div>
<script>
$particle_js
$counter_js
</script>
</body>
</html>"""


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Hot Digest - Archive</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap" rel="stylesheet" />
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
    --bg-primary: #f0f4fa; --bg-card: rgba(255,255,255,0.55); --border-card: rgba(255,255,255,0.25);
    --text-primary: #1e293b; --text-secondary: #334155; --text-muted: #64748b;
    --shadow-card: 0 12px 40px rgba(0,0,0,0.08); --radius-card: 20px;
    --transition-smooth: cubic-bezier(0.22, 1, 0.36, 1);
    --color-dev: #3b82f6;
}
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', -apple-system, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    background: var(--bg-primary); color: var(--text-primary);
    min-height: 100vh; overflow-x: hidden; line-height: 1.7;
}
#bg-canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 0; pointer-events: none; }
.container { position: relative; z-index: 2; max-width: 600px; margin: 0 auto; padding: 48px 24px 64px; }
.header { text-align: center; margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.header h1 {
    font-size: 32px; font-weight: 800; letter-spacing: -0.02em;
    color: var(--text-primary);
    text-shadow: 0 2px 20px rgba(255,255,255,0.5);
}
.header p { font-size: 15px; color: var(--text-secondary); margin-top: 8px; }
.date-list { list-style: none; }
.date-list li {
    background: var(--bg-card); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-card); border-radius: 12px;
    padding: 14px 20px; margin-bottom: 10px; box-shadow: var(--shadow-card);
    transition: transform 0.3s var(--transition-smooth), border-color 0.3s ease;
}
.date-list li:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.5); }
.date-list li a {
    color: var(--text-primary); text-decoration: none; font-size: 16px; font-weight: 600;
}
.date-list li a:hover { color: var(--color-dev, #3b82f6); }
.empty { text-align: center; padding: 60px 20px; color: var(--text-secondary); font-size: 15px; }
.footer { text-align: center; margin-top: 40px; font-size: 12px; color: var(--text-muted); }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 10px; }
</style>
</head>
<body>
<canvas id="bg-canvas"></canvas>
<div class="container">
    <div class="header">
        <h1>Daily Hot Digest</h1>
        <p>自动抓取 GitHub Trending / Lobsters / 少数派 + AI 摘要</p>
    </div>
    $date_list_html
    <div class="footer">
        Powered by GitHub Actions &middot; 每日 UTC 01:00 自动更新
    </div>
</div>
<script>
$particle_js
</script>
</body>
</html>"""


# ============================================================
# 页面生成逻辑
# ============================================================

def generate_daily_page(data: dict, ai_summary: dict | None, date_str: str) -> str:
    """
    生成单日汇总 HTML 页面。
    data: 原始抓取数据
    ai_summary: AI 生成的摘要（可能为 None）
    date_str: 日期字符串 YYYY-MM-DD
    """
    if ai_summary:
        return _generate_from_ai_summary(ai_summary, date_str, data)
    else:
        return _generate_from_raw_data(data, date_str)


def _format_date(date_str: str) -> str:
    """格式化日期为中文显示"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return f"{dt.year} 年 {dt.month} 月 {dt.day} 日 · {weekdays[dt.weekday()]}"
    except ValueError:
        return date_str


def _make_source_color_class(source_name: str) -> str:
    """根据来源名称返回 CSS 颜色 class"""
    for key, color_key in SOURCE_COLOR_MAP.items():
        if key in source_name:
            return color_key
    return "opinion"


def _generate_from_ai_summary(ai_summary: dict, date_str: str, raw_data: dict) -> str:
    """使用 AI 摘要生成页面（段落叙述模式）"""
    categories = ai_summary.get("categories", [])
    sources = ai_summary.get("sources", [])
    stats = ai_summary.get("stats", {})

    # 生成分类 HTML
    categories_html = ""
    for cat in categories:
        color_key = cat.get("color", "ai")
        name = cat.get("name", "未分类")
        summary = cat.get("summary", "")

        # 将 [N] 或 [vN] 转换为带链接的上标引用
        def replace_cite(match):
            num = match.group(1)
            return f'<span class="cite"><a href="#src{num}">[{num}]</a></span>'

        summary_html = re.sub(r'\[v?(\d+)\]', replace_cite, summary)

        # 自动在 GitHub 项目过渡到社区讨论的地方分段
        # 检测 "Lobsters"、"少数派"、"社区" 等关键词前的位置插入换行
        split_patterns = [
            r'(?=Lobsters)',
            r'(?=少数派)',
            r'(?=社区\s*(?:今天|上|里|的))',
            r'(?=\n)',  # 保留模型自己加的换行
        ]
        for pattern in split_patterns:
            summary_html = re.sub(pattern, '\n', summary_html)
        # 清理多余空行
        summary_html = re.sub(r'\n{2,}', '\n', summary_html).strip()

        # 按换行符拆分为多个段落
        paragraphs = summary_html.split('\n')
        paragraphs_html = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())

        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-{color_key}"></span>
      <span class="title"><span class="highlight-{color_key}">{name}</span></span>
    </div>
    {paragraphs_html}
  </div>
"""

    # 生成溯源索引（全局按编号排序）
    sources_sorted = sorted(sources, key=lambda x: x.get("num", 0))

    sources_html = """    <div class="source-group">
      <ul class="source-list">
"""
    for item in sources_sorted:
        num = item.get("num", 0)
        title = item.get("title", "")
        url = item.get("url", "#")
        desc = item.get("desc", "")
        source_name = item.get("source", "")
        color_key = _make_source_color_class(source_name)
        sources_html += (
            f'        <li id="src{num}">'
            f'<span class="num num-{color_key}">{num}</span>'
            f'<a href="{url}" target="_blank">{title}</a> '
            f'<span class="desc">— {desc}</span></li>\n'
        )
    sources_html += "      </ul>\n    </div>\n"

    # 统计
    source_count = len(sources)
    category_count = len(categories)
    item_count = stats.get("total_items", len(sources))

    return _render_template(
        HTML_TEMPLATE,
        date=date_str,
        date_display=_format_date(date_str),
        source_count=source_count,
        category_count=category_count,
        item_count=item_count,
        categories_html=categories_html,
        sources_by_group_html=sources_html,
        color_classes=_generate_color_classes(),
        particle_js=PARTICLE_JS,
        counter_js=COUNTER_JS,
    )


def _generate_from_raw_data(data: dict, date_str: str) -> str:
    """无 AI 摘要时，直接用原始数据生成页面"""
    categories_html = ""
    source_num = 0
    all_sources = []

    # GitHub Trending
    gh_items = data.get("github_trending", [])
    if gh_items:
        gh_tags = ""
        for item in gh_items:
            source_num += 1
            title = item["title"].replace(" / ", "/")
            # 提取 repo 名称 (owner/repo 格式)
            repo_name = title.split(" - ")[0].split(" / ")[0] if " - " in title else title.split(" / ")[0]
            stars = item.get("stars", "")
            stars_display = ""
            if stars:
                try:
                    stars_display = format(int(stars), ",")
                except (ValueError, TypeError):
                    stars_display = stars
            stars_span = f'<span class="gh-stars" data-repo="{repo_name}">{stars_display}</span>' if stars_display else f'<span class="gh-stars" data-repo="{repo_name}">—</span>'
            gh_tags += (
                f'<a class="gh-item" href="{item["url"]}" target="_blank">'
                f'{title}'
                f'{stars_span}'
                f'</a>\n'
            )
            all_sources.append({
                "num": source_num, "title": title, "url": item["url"],
                "source": "GitHub Trending", "desc": item.get("description", "")
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-dev"></span>
      <span class="title"><span class="highlight-dev">GitHub</span> Trending</span>
      <span class="count-badge">{len(gh_items)} repos</span>
    </div>
    <p>{gh_tags}</p>
  </div>
"""

    # Lobsters
    lob_items = data.get("lobsters", [])
    if lob_items:
        lob_list = ""
        for item in lob_items:
            source_num += 1
            tags = item.get("tags", [])
            tag_html = " ".join(
                f'<span style="background:rgba(0,0,0,0.04);padding:0 8px;'
                f'border-radius:4px;font-size:12px;color:var(--text-muted);">{t}</span>'
                for t in tags
            )
            lob_list += (
                f'<li style="margin-bottom:6px;">'
                f'<a href="{item["url"]}" target="_blank" '
                f'style="color:var(--text-secondary);text-decoration:none;font-weight:500;">'
                f'{item["title"]}</a> {tag_html}</li>\n'
            )
            all_sources.append({
                "num": source_num, "title": item["title"], "url": item["url"],
                "source": "Lobsters", "desc": ", ".join(tags)
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-sys"></span>
      <span class="title"><span class="highlight-sys">Lobsters</span> 热帖</span>
      <span class="count-badge">{len(lob_items)} topics</span>
    </div>
    <ul style="list-style:none;padding:0;">{lob_list}</ul>
  </div>
"""

    # 少数派
    sspai_items = data.get("sspai", [])
    if sspai_items:
        sspai_list = ""
        for item in sspai_items:
            source_num += 1
            author = f' <span style="color:var(--text-muted);font-size:12px;">({item.get("author", "")})</span>' if item.get("author") else ""
            sspai_list += (
                f'<li style="margin-bottom:6px;">'
                f'<a href="{item["url"]}" target="_blank" '
                f'style="color:var(--text-secondary);text-decoration:none;font-weight:500;">'
                f'{item["title"]}</a>{author}</li>\n'
            )
            all_sources.append({
                "num": source_num, "title": item["title"], "url": item["url"],
                "source": "少数派", "desc": item.get("author", "")
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-gadget"></span>
      <span class="title"><span class="highlight-gadget">少数派</span>精选</span>
      <span class="count-badge">{len(sspai_items)} articles</span>
    </div>
    <ul style="list-style:none;padding:0;">{sspai_list}</ul>
  </div>
"""

    # 微博热搜
    weibo_items = data.get("weibo", [])
    if weibo_items:
        weibo_list = ""
        for item in weibo_items:
            source_num += 1
            label = item.get("label", "")
            label_html = f' <span style="background:#ff8200;color:#fff;padding:0 6px;border-radius:3px;font-size:11px;font-weight:600;">{label}</span>' if label else ""
            hot = item.get("hot_value", 0)
            hot_html = f' <span style="color:var(--text-muted);font-size:12px;">{hot:,}</span>' if hot else ""
            weibo_list += (
                f'<li style="margin-bottom:6px;">'
                f'<a href="{item["url"]}" target="_blank" '
                f'style="color:var(--text-secondary);text-decoration:none;font-weight:500;">'
                f'{item["title"]}</a>{label_html}{hot_html}</li>\n'
            )
            all_sources.append({
                "num": source_num, "title": item["title"], "url": item["url"],
                "source": "微博热搜", "desc": f"热度 {item.get('hot_value', 0):,}" if item.get("hot_value") else ""
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-opinion"></span>
      <span class="title"><span class="highlight-opinion">微博</span>热搜</span>
      <span class="count-badge">{len(weibo_items)} topics</span>
    </div>
    <ul style="list-style:none;padding:0;">{weibo_list}</ul>
  </div>
"""

    # 知乎热榜
    zhihu_items = data.get("zhihu", [])
    if zhihu_items:
        zhihu_list = ""
        for item in zhihu_items:
            source_num += 1
            excerpt = item.get("excerpt", "")
            excerpt_html = f'<div style="font-size:12px;color:var(--text-muted);margin-top:2px;">{excerpt}</div>' if excerpt else ""
            zhihu_list += (
                f'<li style="margin-bottom:8px;">'
                f'<a href="{item["url"]}" target="_blank" '
                f'style="color:var(--text-secondary);text-decoration:none;font-weight:500;">'
                f'{item["title"]}</a>{excerpt_html}</li>\n'
            )
            all_sources.append({
                "num": source_num, "title": item["title"], "url": item["url"],
                "source": "知乎热榜", "desc": item.get("hot_value", "")
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-opinion"></span>
      <span class="title"><span class="highlight-opinion">知乎</span>热榜</span>
      <span class="count-badge">{len(zhihu_items)} topics</span>
    </div>
    <ul style="list-style:none;padding:0;">{zhihu_list}</ul>
  </div>
"""

    # Hacker News
    hn_items = data.get("hackernews", [])
    if hn_items:
        hn_list = ""
        for item in hn_items:
            source_num += 1
            score = item.get("score", 0)
            comments = item.get("comments", 0)
            meta = f' <span style="color:var(--text-muted);font-size:12px;">{score} pts · {comments} comments</span>'
            hn_list += (
                f'<li style="margin-bottom:6px;">'
                f'<a href="{item["url"]}" target="_blank" '
                f'style="color:var(--text-secondary);text-decoration:none;font-weight:500;">'
                f'{item["title"]}</a>{meta}</li>\n'
            )
            all_sources.append({
                "num": source_num, "title": item["title"], "url": item["url"],
                "source": "Hacker News", "desc": f"{score} pts"
            })
        categories_html += f"""  <div class="card">
    <div class="card-header">
      <span class="dot dot-dev"></span>
      <span class="title"><span class="highlight-dev">Hacker</span> News</span>
      <span class="count-badge">{len(hn_items)} stories</span>
    </div>
    <ul style="list-style:none;padding:0;">{hn_list}</ul>
  </div>
"""

    # 溯源索引（按来源分组）
    sources_by_source = {}
    for src in all_sources:
        sn = src["source"]
        if sn not in sources_by_source:
            sources_by_source[sn] = []
        sources_by_source[sn].append(src)

    sources_html = ""
    for sn, items in sources_by_source.items():
        color_key = _make_source_color_class(sn)
        sources_html += f"""    <div class="source-group">
      <div class="source-group-title">{sn}</div>
      <ul class="source-list">
"""
        for item in items:
            sources_html += (
                f'        <li id="src{item["num"]}">'
                f'<span class="num num-{color_key}">{item["num"]}</span>'
                f'<a href="{item["url"]}" target="_blank">{item["title"]}</a> '
                f'<span class="desc">— {item["desc"]}</span></li>\n'
            )
        sources_html += "      </ul>\n    </div>\n"

    # 计算实际卡片数
    card_count = sum(1 for v in [
        data.get("github_trending", []),
        data.get("lobsters", []),
        data.get("sspai", []),
        data.get("weibo", []),
        data.get("zhihu", []),
        data.get("hackernews", []),
    ] if v)

    return _render_template(
        HTML_TEMPLATE,
        date=date_str,
        date_display=_format_date(date_str),
        source_count=len(sources_by_source),
        category_count=card_count,
        item_count=len(all_sources),
        categories_html=categories_html,
        sources_by_group_html=sources_html,
        color_classes=_generate_color_classes(),
        particle_js=PARTICLE_JS,
        counter_js=COUNTER_JS,
    )


def generate_index_page(site_dir: str) -> str:
    """
    扫描 site_dir 下所有日期命名的 HTML 文件，生成归档首页。
    """
    dates = []
    if os.path.isdir(site_dir):
        for fname in os.listdir(site_dir):
            if fname.endswith(".html") and fname != "index.html" and len(fname) == 15:
                date_str = fname[:-5]
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_str)
                except ValueError:
                    pass

    dates.sort(reverse=True)

    if not dates:
        list_html = '<div class="empty">暂无内容，等待首次自动生成...</div>'
    else:
        list_html = '<ul class="date-list">'
        for d in dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
                weekdays = ["一", "二", "三", "四", "五", "六", "日"]
                display = f"{dt.year}-{dt.month:02d}-{dt.day:02d} 周{weekdays[dt.weekday()]}"
            except ValueError:
                display = d
            list_html += f'<li><a href="{d}.html">{display}</a></li>'
        list_html += '</ul>'

    # 归档页使用精简版粒子（50个）
    index_particle_js = PARTICLE_JS.replace("PARTICLE_COUNT = 100", "PARTICLE_COUNT = 50")

    return _render_template(
        INDEX_TEMPLATE,
        date_list_html=list_html,
        particle_js=index_particle_js,
    )
