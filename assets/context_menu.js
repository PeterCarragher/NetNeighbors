// Right-click context menu for graph area
document.addEventListener('DOMContentLoaded', function() {

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

    // --- Export dropdown toggle ---
    document.addEventListener('click', function(e) {
        var toggler = document.getElementById('export-toggle-btn');
        var dropdown = document.getElementById('export-dropdown');
        if (!toggler || !dropdown) return;

        if (toggler.contains(e.target)) {
            // Toggle
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        } else if (!dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
});
