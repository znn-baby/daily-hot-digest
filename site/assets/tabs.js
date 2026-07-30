/**
 * Daily Hot Digest — Tab Switching
 * AI 简报 / 信息源 视图切换
 */
(function() {
    'use strict';
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
})();
