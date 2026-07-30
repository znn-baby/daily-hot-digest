/**
 * Daily Hot Digest — Particle Background
 * Canvas 粒子网络动画 + 蓝天白云背景
 * 支持 data-particles="N" 属性自定义粒子数量（默认 100）
 */
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

    var bgImage = new Image();
    bgImage.crossOrigin = 'anonymous';
    bgImage.src = 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80';
    var bgLoaded = false;
    bgImage.onload = function() { bgLoaded = true; };
    bgImage.onerror = function() { bgLoaded = false; };

    var particles = [];
    var PARTICLE_COUNT = parseInt(canvas.dataset.particles) || 100;
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
                drawH = H; drawW = H * imgAspect; offsetX = (W - drawW) / 2; offsetY = 0;
            } else {
                drawW = W; drawH = W / imgAspect; offsetX = 0; offsetY = (H - drawH) / 2;
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
