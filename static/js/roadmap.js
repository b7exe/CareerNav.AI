/**
 * roadmap.js — Roadmap Page Interactions
 * ========================================
 * - Phase accordion expand / collapse
 * - Subtopic completion toggle (localStorage-persisted)
 * - Progress bar updates (synced across sidebar + header panels)
 * - Sidebar active-phase tracking via IntersectionObserver
 * - Home page chip → prompt fill (handled in transitions.js)
 */
(function () {
    'use strict';

    // ─────────────────────────────────────────────────────────────────
    // 1. PHASE ACCORDION
    // ─────────────────────────────────────────────────────────────────
    const phaseCards = document.querySelectorAll('.roadmap-phase-card');
    if (phaseCards.length === 0) return; // not on roadmap page

    const slug       = document.body.dataset.roadmapSlug || 'roadmap';
    const storageKey = 'completed_' + slug;
    let completed    = new Set(JSON.parse(localStorage.getItem(storageKey) || '[]'));

    // Open first phase by default
    openPhase(phaseCards[0]);

    phaseCards.forEach(function (card) {
        const header = card.querySelector('.phase-header');
        if (!header) return;

        // Click to toggle
        header.addEventListener('click', function () {
            const isOpen = card.classList.contains('is-open');
            // Close all phases first
            phaseCards.forEach(function (c) { c.classList.remove('is-open'); });
            // Re-open if it was closed before click
            if (!isOpen) openPhase(card);
        });

        // Keyboard support (Enter / Space)
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                header.click();
            }
        });

        // Subtopic completion toggles
        card.querySelectorAll('.subtopic-item').forEach(function (item) {
            const topicId = item.dataset.topicId;
            if (!topicId) return;

            // Restore persisted state
            if (completed.has(topicId)) markDone(item, true);

            item.addEventListener('click', function () {
                const nowDone = !item.classList.contains('completed');
                markDone(item, nowDone);
                if (nowDone) completed.add(topicId);
                else         completed.delete(topicId);
                localStorage.setItem(storageKey, JSON.stringify([...completed]));
                updateProgress();
            });

            // Keyboard support
            item.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    item.click();
                }
            });
        });
    });

    // Render initial progress
    updateProgress();

    // Staggered entrance animation delays
    phaseCards.forEach(function (card, i) {
        card.style.animationDelay = (i * 55) + 'ms';
    });

    // ─── helpers ──────────────────────────────────────────────────────
    function openPhase(card) {
        if (!card) return;
        card.classList.add('is-open');
        const header = card.querySelector('.phase-header');
        if (header) header.setAttribute('aria-expanded', 'true');
    }

    function markDone(item, done) {
        item.classList.toggle('completed', done);
        item.setAttribute('aria-checked', done ? 'true' : 'false');

        const check = item.querySelector('.subtopic-check');
        if (!check) return;
        check.innerHTML = done
            ? '<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1.5 5L4 7.5L8.5 2.5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            : '';
    }

    function updateProgress() {
        const total = parseInt(document.body.dataset.totalTopics || '0', 10);
        if (!total) return;

        const count = completed.size;
        const pct   = Math.round((count / total) * 100);
        const text  = count + ' of ' + total + ' topics completed';

        // Sidebar + mobile bars
        ['progress-fill', 'progress-fill-mobile'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.style.width = pct + '%';
        });
        ['progress-label', 'progress-label-mobile'].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.textContent = id.includes('mobile')
                ? count + ' of ' + total + ' done'
                : text;
        });
    }

    // ─────────────────────────────────────────────────────────────────
    // 2. SIDEBAR ACTIVE PHASE (IntersectionObserver)
    // ─────────────────────────────────────────────────────────────────
    const sidebarItems = document.querySelectorAll('.roadmap-sidebar-item[data-phase]');

    if (sidebarItems.length > 0) {
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                const idx = entry.target.dataset.phaseIndex;
                sidebarItems.forEach(function (si) {
                    si.classList.toggle('active', si.dataset.phase === idx);
                });
            });
        }, { rootMargin: '-15% 0px -70% 0px' });

        phaseCards.forEach(function (card) { observer.observe(card); });

        // Sidebar click → open + scroll
        sidebarItems.forEach(function (item) {
            item.addEventListener('click', function () {
                const idx    = item.dataset.phase;
                const target = document.querySelector(
                    '.roadmap-phase-card[data-phase-index="' + idx + '"]'
                );
                if (!target) return;
                phaseCards.forEach(function (c) { c.classList.remove('is-open'); });
                openPhase(target);
                setTimeout(function () {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 50);
            });
        });
    }

})();
