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

    // --- Presenter search: built entirely in vanilla JS so React never touches it ---
    var _searchDropdown = null;
    var _searchHighlightIdx = -1;
    var _searchInput = null;   // set once widget is created

    function getSearchDropdown() {
        if (_searchDropdown) return _searchDropdown;
        var d = document.createElement('div');
        d.style.cssText = [
            'position:fixed',
            'z-index:99999',
            'display:none',
            'background:rgba(45,45,45,0.92)',
            'border:1px solid rgba(255,255,255,0.15)',
            'border-radius:5px',
            'overflow:hidden',
            'backdrop-filter:blur(6px)',
            'box-shadow:0 4px 16px rgba(0,0,0,0.45)',
        ].join(';');
        document.body.appendChild(d);
        _searchDropdown = d;
        return d;
    }

    function hideSearchDropdown() {
        getSearchDropdown().style.display = 'none';
        _searchHighlightIdx = -1;
    }

    function setDropdownHighlight(idx) {
        var items = getSearchDropdown().children;
        for (var i = 0; i < items.length; i++) {
            items[i].style.background = i === idx ? 'rgba(102,126,234,0.55)' : '';
        }
        _searchHighlightIdx = idx;
    }

    function closeSearch() {
        if (_searchInput) _searchInput.style.display = 'none';
        _searchInput && (_searchInput.value = '');
        hideSearchDropdown();
    }

    function selectSearchNode(nodeId) {
        var bridge = document.getElementById('presenter-select-bridge');
        if (bridge) {
            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(bridge, nodeId + '|||' + Date.now());
            bridge.dispatchEvent(new Event('input', { bubbles: true }));
        }
        closeSearch();
    }

    function showSearchResults() {
        var inputEl = _searchInput;
        if (!inputEl) return;
        var q = (inputEl.value || '').trim().toLowerCase();
        if (!q) { hideSearchDropdown(); return; }

        var nodes = window._graphNodes || [];
        var matches = [];
        for (var i = 0; i < nodes.length && matches.length < 3; i++) {
            var n = nodes[i];
            if ((n.id || '').toLowerCase().indexOf(q) >= 0 ||
                    (n.label || '').toLowerCase().indexOf(q) >= 0) {
                matches.push(n.id);
            }
        }

        var d = getSearchDropdown();
        d.innerHTML = '';
        if (!matches.length) { d.style.display = 'none'; return; }

        matches.forEach(function(nodeId, idx) {
            var item = document.createElement('div');
            item.textContent = nodeId;
            item.style.cssText = [
                'padding:8px 14px',
                'color:rgba(255,255,255,0.9)',
                "font-family:'Space Mono',monospace",
                'font-size:12px',
                'cursor:pointer',
                'white-space:nowrap',
                'overflow:hidden',
                'text-overflow:ellipsis',
            ].join(';');
            item.addEventListener('mouseover', function() { setDropdownHighlight(idx); });
            item.addEventListener('mousedown', function(e) {
                e.preventDefault();
                selectSearchNode(nodeId);
            });
            d.appendChild(item);
        });

        var rect = inputEl.getBoundingClientRect();
        d.style.left = rect.left + 'px';
        d.style.top = (rect.bottom + 4) + 'px';
        d.style.minWidth = rect.width + 'px';
        d.style.display = 'block';
        _searchHighlightIdx = -1;
    }

    // Build the widget DOM and mount to body — zero React involvement
    (function buildPresenterSearch() {
        var container = document.createElement('div');
        container.style.cssText = [
            'position:fixed',
            'top:8px',
            'left:calc(50% - 40px)',
            'transform:translateX(-50%)',
            'z-index:9000',
            'display:none',   // shown by MutationObserver when presenter mode activates
            'align-items:center',
            'gap:6px',
        ].join(';');

        var toggleBtn = document.createElement('div');
        toggleBtn.title = 'Search domains';
        toggleBtn.style.cssText = [
            'cursor:pointer',
            'padding:7px 9px',
            'background:rgba(255,255,255,0.88)',
            'border:1px solid #ddd',
            'border-radius:5px',
            'font-size:14px',
            'color:#555',
            'line-height:1',
            'flex-shrink:0',
            'user-select:none',
        ].join(';');
        toggleBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass" style="pointer-events:none"></i>';

        var inputEl = document.createElement('input');
        inputEl.type = 'text';
        inputEl.placeholder = 'search domains...';
        inputEl.style.cssText = [
            'display:none',
            'width:240px',
            'background:rgba(55,55,55,0.62)',
            'border:1px solid rgba(255,255,255,0.22)',
            'border-radius:5px',
            'color:#fff',
            'padding:6px 12px',
            "font-family:'Space Mono',monospace",
            'font-size:13px',
            'outline:none',
            'box-sizing:border-box',
        ].join(';');
        // Placeholder colour via a stylesheet rule (can't set via inline style)
        var phStyle = document.createElement('style');
        phStyle.textContent = '#_ps_input::placeholder{color:rgba(255,255,255,0.45);}';
        document.head.appendChild(phStyle);
        inputEl.id = '_ps_input';

        container.appendChild(toggleBtn);
        container.appendChild(inputEl);
        document.body.appendChild(container);
        _searchInput = inputEl;

        // Show/hide the whole widget when presenter mode toggles
        (function watchPresenterMode() {
            var rootEl = document.getElementById('root-container');
            if (!rootEl) { setTimeout(watchPresenterMode, 100); return; }
            new MutationObserver(function() {
                var isPresenter = rootEl.classList.contains('presenter-mode');
                container.style.display = isPresenter ? 'flex' : 'none';
                if (!isPresenter) closeSearch();
            }).observe(rootEl, { attributes: true, attributeFilter: ['class'] });
        })();

        // Toggle the input open/closed
        toggleBtn.addEventListener('click', function() {
            if (inputEl.style.display === 'block') {
                closeSearch();
            } else {
                inputEl.style.display = 'block';
                inputEl.focus();
            }
        });

        inputEl.addEventListener('input', showSearchResults);

        inputEl.addEventListener('keydown', function(e) {
            var items = getSearchDropdown().children;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setDropdownHighlight(Math.min(_searchHighlightIdx + 1, items.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setDropdownHighlight(Math.max(_searchHighlightIdx - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                var idx = _searchHighlightIdx >= 0 ? _searchHighlightIdx : 0;
                var node = items[idx];
                if (node) selectSearchNode(node.textContent);
            } else if (e.key === 'Escape') {
                closeSearch();
            }
        });

        inputEl.addEventListener('blur', function() {
            setTimeout(hideSearchDropdown, 150);
        });

        // Close on click outside the widget
        document.addEventListener('mousedown', function(e) {
            if (inputEl.style.display === 'block' && !container.contains(e.target)) {
                closeSearch();
            }
        });
    })();
});
