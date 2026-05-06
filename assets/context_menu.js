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

    // --- Legend swatch color picker ---
    // Popup created once, reused for every right-click.
    var colorPickerHop = null;
    var colorPickerPopup = (function() {
        var popup = document.createElement('div');
        popup.style.cssText = [
            'position:fixed',
            'z-index:10000',
            'display:none',
            'background:white',
            'border:1px solid #ddd',
            'border-radius:6px',
            'padding:6px 8px',
            'box-shadow:0 3px 12px rgba(0,0,0,0.18)',
            'align-items:center',
            'gap:6px',
            'font-size:12px',
            'font-family:Space Mono,monospace',
            'color:#555',
        ].join(';');

        var label = document.createElement('span');
        label.textContent = 'color';
        popup.appendChild(label);

        var input = document.createElement('input');
        input.type = 'color';
        input.style.cssText = 'width:32px;height:28px;border:none;padding:0;cursor:pointer;border-radius:3px;background:none;';
        input.addEventListener('input', function() {
            writeToBridge(colorPickerHop, input.value);
        });
        popup.appendChild(input);
        document.body.appendChild(popup);
        return { popup: popup, input: input };
    })();

    function writeToBridge(hop, color) {
        var bridge = document.getElementById('color-pick-bridge');
        if (!bridge) return;
        // Use React's internal setter so the synthetic onChange fires
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(bridge, hop + '|||' + color + '|||' + Date.now());
        bridge.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // --- Right-click handler (swatches + graph context menu) ---
    document.addEventListener('contextmenu', function(e) {

        // 1. Check if right-clicking a legend swatch
        var el = e.target;
        var swatchEl = null;
        while (el && el !== document.body) {
            if (el.id && el.id.indexOf('"legend-swatch"') >= 0) {
                swatchEl = el;
                break;
            }
            el = el.parentElement;
        }

        if (swatchEl) {
            e.preventDefault();
            e.stopImmediatePropagation();

            try {
                var idObj = JSON.parse(swatchEl.id);
                colorPickerHop = String(idObj.index);
            } catch(_) { return; }

            // Seed color input with current swatch color, converting rgb→hex if needed
            var bg = swatchEl.style.background || '#ff6b6b';
            if (bg.startsWith('rgb')) {
                var parts = bg.match(/\d+/g);
                if (parts && parts.length >= 3) {
                    bg = '#' + parts.slice(0, 3).map(function(x) {
                        return ('0' + parseInt(x).toString(16)).slice(-2);
                    }).join('');
                }
            }
            colorPickerPopup.input.value = bg;

            var p = colorPickerPopup.popup;
            p.style.display = 'flex';
            // Keep popup within viewport
            var pw = 110, ph = 44;
            var left = Math.min(e.clientX, window.innerWidth - pw - 8);
            var top = Math.min(e.clientY, window.innerHeight - ph - 8);
            p.style.left = left + 'px';
            p.style.top = top + 'px';
            return;
        }

        // 2. Graph-wrapper context menu
        var wrapper = document.getElementById('graph-wrapper');
        if (!wrapper || !wrapper.contains(e.target)) return;

        e.preventDefault();
        var menu = document.getElementById('context-menu');
        if (!menu) return;

        var rect = wrapper.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;

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
        // Close color picker on outside click
        var p = colorPickerPopup.popup;
        if (p.style.display !== 'none' && !p.contains(e.target)) {
            p.style.display = 'none';
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
