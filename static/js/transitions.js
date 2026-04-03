/**
 * transitions.js — SPA-style Page Transitions
 * =============================================
 * Intercepts all internal link clicks and form submissions.
 * 1. Tears down the neural cursor (home-page only, no-op elsewhere)
 * 2. Fades out + slides up the page-transition-wrapper
 * 3. Shows the loading overlay (cyan spinner — matches original theme)
 * 4. Navigates to the new URL
 * On page load, triggers the fade-in entrance animation.
 */
(function () {
    'use strict';

    const DURATION = 320; // ms — matches CSS transition duration

    // ── Loading overlay ───────────────────────────────────────────────
    const overlay   = document.getElementById('loading-overlay');
    const overlayTxt = overlay ? overlay.querySelector('.loading-text') : null;

    function showLoading(text) {
        if (!overlay) return;
        if (overlayTxt && text) overlayTxt.textContent = text;
        overlay.classList.add('active');
    }

    function hideLoading() {
        if (overlay) overlay.classList.remove('active');
    }

    // ── Page wrapper ──────────────────────────────────────────────────
    const wrapper = document.querySelector('.page-transition-wrapper');

    function navigateTo(href, loadingText) {
        // 1. Destroy neural cursor cleanly (avoids orphaned RAF on next page)
        if (window._neuralCursor && typeof window._neuralCursor.destroy === 'function') {
            window._neuralCursor.destroy();
        }

        // 2. Exit animation + show loader
        if (wrapper) {
            wrapper.classList.add('page-exit');
        }
        showLoading(loadingText || 'Loading…');

        // 3. Navigate after animation completes
        setTimeout(function () {
            window.location.href = href;
        }, DURATION);
    }

    // ── Intercept <a> clicks ──────────────────────────────────────────
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[href]');
        if (!link) return;

        const href = link.getAttribute('href');

        // Skip: external, hash-only, javascript:, new-tab, opted-out
        if (
            !href ||
            href.startsWith('http://') ||
            href.startsWith('https://') ||
            href.startsWith('#') ||
            href.startsWith('javascript:') ||
            link.target === '_blank' ||
            link.dataset.noTransition !== undefined ||
            e.ctrlKey || e.metaKey || e.shiftKey
        ) return;

        e.preventDefault();

        let label = 'Loading…';
        if (href.includes('/roadmap'))    label = 'Generating roadmap…';
        else if (href.includes('/dashboard'))  label = 'Loading dashboard…';
        else if (href.includes('/assessment')) label = 'Loading assessment…';

        navigateTo(href, label);
    }, false);

    // ── Home page prompt form ─────────────────────────────────────────
    // Enhances the form submit so it uses the animated transition instead
    // of a bare browser GET request.
    document.addEventListener('DOMContentLoaded', function () {
        const form  = document.getElementById('prompt-form');
        const input = document.getElementById('prompt-input');

        if (form && input) {
            form.addEventListener('submit', function (e) {
                const val = input.value.trim();
                if (!val) return; // let browser show native validation

                e.preventDefault();
                navigateTo('/roadmap?q=' + encodeURIComponent(val), 'Generating roadmap…');
            });
        }

        // Roadmap chips (home page)
        document.querySelectorAll('.roadmap-chip[data-slug]').forEach(function (chip) {
            chip.addEventListener('click', function () {
                navigateTo('/roadmap?q=' + encodeURIComponent(chip.dataset.slug), 'Generating roadmap…');
            });
        });
    });

    // ── Entrance animation ────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        hideLoading();
        if (!wrapper) return;

        wrapper.classList.add('page-enter');
        // Remove class after animation so it doesn't interfere with hover states
        setTimeout(function () {
            wrapper.classList.remove('page-enter');
        }, DURATION + 80);
    });

    // Expose for external use (e.g., roadmap.js)
    window._appNav = { navigateTo };

})();
