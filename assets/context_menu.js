// Named clientside function for domain-list multi-select (shift/ctrl-click).
// Defined here so Dash can look it up reliably via ClientsideFunction rather
// than relying on the auto-generated inline-callback hash.
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: Object.assign({}, (window.dash_clientside || {}).clientside, {
        domain_click_handler: function(n_clicks_list, current_selected, all_nodes, search_text, last_clicked) {
            var ctx = dash_clientside.callback_context;
            if (!ctx || !ctx.triggered || !ctx.triggered.length) {
                throw dash_clientside.PreventUpdate;
            }
            if (!n_clicks_list || !n_clicks_list.some(function(n) { return n; })) {
                throw dash_clientside.PreventUpdate;
            }

            var triggered = ctx.triggered[0];
            var id_obj = JSON.parse(triggered.prop_id.split('.n_clicks')[0]);
            var domain = id_obj.index;

            var domains = (all_nodes || []).map(function(n) { return n.id; }).sort();
            if (search_text) {
                var q = search_text.toLowerCase();
                domains = domains.filter(function(d) { return d.toLowerCase().indexOf(q) >= 0; });
            }

            current_selected = current_selected || [];
            var mod = window._lastModifiers || {};

            var newSelected;
            if (mod.ctrl) {
                var already = current_selected.indexOf(domain);
                newSelected = already >= 0
                    ? current_selected.filter(function(d) { return d !== domain; })
                    : current_selected.concat([domain]);
            } else if (mod.shift && last_clicked && domains.indexOf(last_clicked) >= 0) {
                var a = domains.indexOf(last_clicked);
                var b = domains.indexOf(domain);
                var lo = Math.min(a, b), hi = Math.max(a, b);
                newSelected = domains.slice(lo, hi + 1);
            } else {
                newSelected = [domain];
            }

            return [domain, newSelected, domain];
        }
    })
});

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

    // Capture modifier key state on mousedown so clientside callbacks can reliably read it.
    // window.event is stale by the time Dash fires its callbacks, but _lastModifiers is set first.
    window._lastModifiers = { ctrl: false, shift: false };
    document.addEventListener('mousedown', function(e) {
        window._lastModifiers = { ctrl: e.ctrlKey || e.metaKey, shift: e.shiftKey };
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
            var btn = document.getElementById('delete-btn');
            if (btn) btn.click();
        }
    });
});
