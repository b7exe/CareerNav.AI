/**
 * cursor.js — Gradient Orb Cursor (Home Page Only)
 * ==================================================
 * Renders a large, soft radial-gradient blob that smoothly
 * lerp-follows the mouse. Inspired by Vercel/Antigravity style.
 *
 * GUARD: Checks body[data-page] === "home" immediately.
 * On any other page this is a complete no-op — no events, no RAF.
 */
(function () {
    'use strict';

    // ── Home-page guard ───────────────────────────────────────────
    if (document.body.dataset.page !== 'home') return;

    // ── Find the orb div (injected in base.html on home only) ─────
    const orb = document.getElementById('cursor-orb');
    if (!orb) return;

    // ── State ─────────────────────────────────────────────────────
    let targetX  = window.innerWidth  / 2;
    let targetY  = window.innerHeight / 2;
    let currentX = targetX;
    let currentY = targetY;
    let rafId    = null;
    let active   = false;

    // Lerp factor — lower = smoother, lazier follow (Vercel uses ~0.08)
    const LERP = 0.08;

    // ── Activate on first mouse move ──────────────────────────────
    function activate() {
        if (active) return;
        active = true;
        orb.classList.add('active');
        tick();
    }

    // ── Track pointer ─────────────────────────────────────────────
    window.addEventListener('mousemove', function (e) {
        targetX = e.clientX;
        targetY = e.clientY;
        activate();
    }, { passive: true });

    window.addEventListener('touchmove', function (e) {
        if (e.touches.length > 0) {
            targetX = e.touches[0].clientX;
            targetY = e.touches[0].clientY;
            activate();
        }
    }, { passive: true });

    // ── RAF animation loop ─────────────────────────────────────────
    function tick() {
        // Lerp towards target
        currentX += (targetX - currentX) * LERP;
        currentY += (targetY - currentY) * LERP;

        // Position the orb centred on the cursor
        // CSS already sets transform: translate(-50%, -50%)
        orb.style.left = currentX + 'px';
        orb.style.top  = currentY + 'px';

        rafId = requestAnimationFrame(tick);
    }

    // ── Cleanup when navigating away ──────────────────────────────
    // transitions.js calls this before navigating
    window._neuralCursor = {
        destroy: function () {
            if (rafId) cancelAnimationFrame(rafId);
            orb.classList.remove('active');
        }
    };

})();
