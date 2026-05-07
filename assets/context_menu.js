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

    // --- Loading cursor (FA spinner that follows the mouse) ---
    var _cursorX = window.innerWidth / 2;
    var _cursorY = window.innerHeight / 2;
    var _loadingEl = null;
    var _loadingTimer = null;

    // Inject the keyframe once so the inline animation works on dynamically created elements.
    // We do NOT rely on fa-spin because FA's CSS may not apply to imperatively-created nodes.
    (function() {
        var s = document.createElement('style');
        s.textContent = '@keyframes _lc_spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}';
        document.head.appendChild(s);
    })();

    document.addEventListener('mousemove', function(e) {
        _cursorX = e.clientX;
        _cursorY = e.clientY;
        if (_loadingEl && _loadingEl.style.display !== 'none') {
            _loadingEl.style.left = _cursorX + 'px';
            _loadingEl.style.top  = _cursorY + 'px';
        }
    });

    window._showLoadingCursor = function() {
        if (!_loadingEl) {
            _loadingEl = document.createElement('div');
            _loadingEl.style.cssText = [
                'position:fixed',
                'pointer-events:none',
                'z-index:999999',
                'display:none',
                'font-size:18px',
                'color:#667eea',
                'transform:translate(-50%,-50%)',
                'line-height:1',
            ].join(';');
            var icon = document.createElement('i');
            icon.className = 'fa-solid fa-circle-notch fa-2x';
            icon.style.cssText = 'display:inline-block;animation:_lc_spin 0.75s linear infinite;';
            _loadingEl.appendChild(icon);
            document.body.appendChild(_loadingEl);
        }
        _loadingEl.style.left = _cursorX + 'px';
        _loadingEl.style.top  = _cursorY + 'px';
        _loadingEl.style.display = 'block';
        document.body.style.cursor = 'none';
        // Safety: auto-hide after 60 s in case the callback never fires
        if (_loadingTimer) clearTimeout(_loadingTimer);
        _loadingTimer = setTimeout(window._hideLoadingCursor, 60000);
    };

    window._hideLoadingCursor = function() {
        if (_loadingTimer) { clearTimeout(_loadingTimer); _loadingTimer = null; }
        if (_loadingEl) _loadingEl.style.display = 'none';
        document.body.style.cursor = '';
    };

    // Show on discover-btn click (event delegation — safe even if btn re-renders)
    document.addEventListener('click', function(e) {
        var t = e.target;
        while (t && t !== document.body) {
            if (t.id === 'discover-btn') { window._showLoadingCursor(); break; }
            t = t.parentElement;
        }
    });

    // --- Presenter search: built entirely in vanilla JS so React never touches it ---

    // Called by clientside callback when presenter-add-result changes.
    // Shows a red flash + "not found" hint in the dropdown for failed adds.
    window._psHandleAddResult = function(result) {
        if (!result || !_searchInput) return;
        var parts = result.split('|||');
        var status = parts[0];
        var domain = parts[1] || '';
        if (status === 'not_found' || status === 'invalid') {
            // Flash input red
            _searchInput.style.borderColor = 'rgba(231,76,60,0.85)';
            _searchInput.style.background = 'rgba(231,76,60,0.18)';
            setTimeout(function() {
                if (_searchInput) {
                    _searchInput.style.borderColor = 'rgba(255,255,255,0.22)';
                    _searchInput.style.background = 'rgba(55,55,55,0.62)';
                }
            }, 1500);
            // Show error message in dropdown
            var d = getSearchDropdown();
            d.innerHTML = '';
            var errEl = document.createElement('div');
            errEl.textContent = status === 'invalid'
                ? '"' + domain + '" is not a valid domain'
                : '"' + domain + '" not found in CommonCrawl';
            errEl.style.cssText = [
                'padding:8px 14px',
                'color:rgba(231,76,60,0.9)',
                "font-family:'Space Mono',monospace",
                'font-size:11px',
                'font-style:italic',
            ].join(';');
            d.appendChild(errEl);
            d.style.display = 'block';
            if (_searchInput) {
                var rect = _searchInput.getBoundingClientRect();
                d.style.left = rect.left + 'px';
                d.style.top = (rect.bottom + 4) + 'px';
                d.style.minWidth = rect.width + 'px';
            }
            setTimeout(function() { hideSearchDropdown(); }, 2500);
        }
    };

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
        if (_searchInput) {
            _searchInput.style.display = 'none';
            _searchInput.value = '';
        }
        hideSearchDropdown();
    }

    function writeBridge(id, value) {
        var bridge = document.getElementById(id);
        if (!bridge) return;
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(bridge, value + '|||' + Date.now());
        bridge.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function selectSearchNode(nodeId, hop, isHidden) {
        // 3-part bridge value tells Dash to unhide the hop before selecting
        var value = isHidden ? nodeId + '|||' + hop : nodeId;
        writeBridge('presenter-select-bridge', value);
        closeSearch();
    }

    function addNewDomain(domain) {
        writeBridge('presenter-add-bridge', domain);
        window._showLoadingCursor();
        closeSearch();
    }

    function showSearchResults() {
        var inputEl = _searchInput;
        if (!inputEl) return;
        var raw = (inputEl.value || '').trim();
        var q = raw.toLowerCase();
        if (!q) { hideSearchDropdown(); return; }

        var nodes = window._graphNodes || [];
        var hiddenHops = window._hiddenHops || new Set();
        var matches = [];
        for (var i = 0; i < nodes.length && matches.length < 3; i++) {
            var n = nodes[i];
            if ((n.id || '').toLowerCase().indexOf(q) >= 0 ||
                    (n.label || '').toLowerCase().indexOf(q) >= 0) {
                matches.push({ id: n.id, hop: n.hop, hidden: hiddenHops.has(n.hop) });
            }
        }

        var d = getSearchDropdown();
        d.innerHTML = '';

        if (!matches.length) {
            // Show hint to add as new domain
            var hint = document.createElement('div');
            hint.textContent = 'add "' + raw + '" to graph (Enter)';
            hint.style.cssText = [
                'padding:8px 14px',
                'color:rgba(255,255,255,0.45)',
                "font-family:'Space Mono',monospace",
                'font-size:11px',
                'cursor:pointer',
                'font-style:italic',
            ].join(';');
            hint.addEventListener('mouseover', function() { hint.style.color = 'rgba(255,255,255,0.8)'; });
            hint.addEventListener('mouseout',  function() { hint.style.color = 'rgba(255,255,255,0.45)'; });
            hint.addEventListener('mousedown', function(e) { e.preventDefault(); addNewDomain(raw); });
            d.appendChild(hint);
        } else {
            matches.forEach(function(match, idx) {
                var item = document.createElement('div');
                item.style.cssText = [
                    'padding:8px 14px',
                    match.hidden ? 'color:rgba(255,255,255,0.45)' : 'color:rgba(255,255,255,0.9)',
                    "font-family:'Space Mono',monospace",
                    'font-size:12px',
                    'cursor:pointer',
                    'white-space:nowrap',
                    'overflow:hidden',
                    'text-overflow:ellipsis',
                    'display:flex',
                    'align-items:center',
                    'gap:6px',
                ].join(';');

                if (match.hidden) {
                    var icon = document.createElement('i');
                    icon.className = 'fa-solid fa-eye-slash';
                    icon.style.cssText = 'font-size:10px;flex-shrink:0;pointer-events:none;';
                    item.appendChild(icon);
                }
                var label = document.createElement('span');
                label.textContent = match.id;
                label.style.overflow = 'hidden';
                label.style.textOverflow = 'ellipsis';
                item.appendChild(label);

                item.addEventListener('mouseover', function() { setDropdownHighlight(idx); });
                item.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    selectSearchNode(match.id, match.hop, match.hidden);
                });
                d.appendChild(item);
            });
        }

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
            var d = getSearchDropdown();
            var items = d.children;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                // skip the hint row (only 1 child = no-results hint, not navigable)
                if (items.length > 1) setDropdownHighlight(Math.min(_searchHighlightIdx + 1, items.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (items.length > 1) setDropdownHighlight(Math.max(_searchHighlightIdx - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                var raw = (inputEl.value || '').trim();
                if (!raw) return;
                // No-results case: hint row is the only child — add domain
                if (items.length === 1 && d.style.display === 'block' && _searchHighlightIdx < 0) {
                    addNewDomain(raw);
                    return;
                }
                var idx = _searchHighlightIdx >= 0 ? _searchHighlightIdx : 0;
                var item = items[idx];
                if (item) item.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
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
