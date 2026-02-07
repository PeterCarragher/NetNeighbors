// Right-click context menu and performance setup for graph area
document.addEventListener('DOMContentLoaded', function() {

    // --- Cytoscape.js renderer performance options ---
    // These can't be set via dash-cytoscape props; must be set on the cy instance.
    // textureOnViewport: renders to a texture during pan/zoom (faster redraws)
    // hideEdgesOnViewport: skips edge drawing during pan/zoom
    // hideLabelsOnViewport: skips label drawing during pan/zoom
    (function initCyPerformance() {
        var cyEl = document.getElementById('cytoscape-graph');
        if (!cyEl || !cyEl._cyreg || !cyEl._cyreg.cy) {
            setTimeout(initCyPerformance, 200);
            return;
        }
        var r = cyEl._cyreg.cy.renderer();
        if (r && r.options) {
            r.options.textureOnViewport = true;
            r.options.hideEdgesOnViewport = true;
            r.options.hideLabelsOnViewport = true;
        }
    })();

    // --- Right-click context menu ---
    document.addEventListener('contextmenu', function(e) {
        var wrapper = document.getElementById('graph-wrapper');
        if (!wrapper || !wrapper.contains(e.target)) return;

        e.preventDefault();
        var menu = document.getElementById('context-menu');
        if (!menu) return;

        // Position relative to graph-wrapper
        var rect = wrapper.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;

        // Keep menu within wrapper bounds
        var menuW = 260;
        var menuH = 280;
        if (x + menuW > rect.width) x = rect.width - menuW - 8;
        if (y + menuH > rect.height) y = rect.height - menuH - 8;
        if (x < 0) x = 8;
        if (y < 0) y = 8;

        menu.style.left = x + 'px';
        menu.style.top = y + 'px';
        menu.style.display = 'block';
    });

    // Dismiss context menu on mousedown outside
    document.addEventListener('mousedown', function(e) {
        var menu = document.getElementById('context-menu');
        if (menu && menu.style.display === 'block' && !menu.contains(e.target)) {
            menu.style.display = 'none';
        }
    });

    // --- Delete key handler ---
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            // Don't trigger if user is typing in an input/textarea
            var tag = document.activeElement && document.activeElement.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

            e.preventDefault();
            var btn = document.getElementById('delete-trigger-btn');
            if (btn) btn.click();
        }
    });
});
