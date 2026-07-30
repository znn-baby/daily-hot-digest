/**
 * Daily Hot Digest — Counter & GitHub Stars
 * 统计数字动画 + GitHub Stars 实时获取
 */
(function() {
    'use strict';

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
