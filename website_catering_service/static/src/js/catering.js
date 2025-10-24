odoo.define('custom_website_catering.catering', function (require) {
    'use strict';

    let selectedItems = [];

    // === HARD-CODED DEFAULT ITEMS TO CHECK ON PAGE LOAD ===
    const DEFAULT_ITEMS = [
        "Lemon juice",
        "Chicken Ghee Roast",
        "Chicken 65",
        "Chicken Pepper Masala",
        "Chicken Biryani (Donne / Hyderabadi)",
        "ice cream",
        "Banana"
    ];

    const BLOCKED_KEYS = ['catering_selected_items', 'cateringData'];

    // Prevent anything from restoring old selections via localStorage
    function blockLocalStorageRestore() {
        try {
            // Remove current values
            BLOCKED_KEYS.forEach(k => localStorage.removeItem(k));
            // Monkey-patch getItem so it returns null for our keys
            const _getItem = localStorage.getItem.bind(localStorage);
            localStorage.getItem = function (key) {
                if (BLOCKED_KEYS.includes(key)) return null;
                return _getItem(key);
            };
            // Also nuke any external writes immediately
            const _setItem = localStorage.setItem.bind(localStorage);
            localStorage.setItem = function (key, val) {
                if (BLOCKED_KEYS.includes(key)) return; // ignore writes to our keys
                return _setItem(key, val);
            };
            window.addEventListener('storage', (e) => {
                if (BLOCKED_KEYS.includes(e.key)) {
                    try { localStorage.removeItem(e.key); } catch(_) {}
                }
            });
        } catch (e) {}
    }

    // Save items to localStorage (kept for addItem, but not used on load)
    function saveItems() {
        // This still works for other keys, but our two keys are blocked above
        try { localStorage.setItem('catering_selected_items', JSON.stringify(selectedItems)); } catch(e){}
    }

    // (DISABLED) Load items from localStorage – not called anymore
    function loadItems() {
        const saved = null; // always null due to block
        if (saved) {
            selectedItems = JSON.parse(saved);
            renderItems();
        }
    }

    function renderItems() {
        const container = document.getElementById('menuItemsContainer');
        if (!container) return; // Avoid error if element missing
        container.innerHTML = '';
        selectedItems.forEach((item) => {
            const div = document.createElement('div');
            div.className = 'col-md-4 mb-3';
            div.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${item.name}</h5>
                        <p class="card-text">Price: ₹${item.price}</p>
                        <p class="card-text">Category: ${item.category}</p>
                    </div>
                </div>`;
            container.appendChild(div);
        });
    }

    // === RESET ALL SELECTIONS ===
    function resetSelections() {
        // Uncheck every menu item + normalize qty
        const scope = document;
        scope.querySelectorAll('input.menu-item[type="checkbox"], .catering-card input[type="checkbox"], .card input[type="checkbox"]')
            .forEach(cb => {
                cb.checked = false;
                const row = cb.closest('.menu-line, .d-flex, .form-check, .o_catering_line, .card, .list-group-item');
                const qty = row && row.querySelector('.qty-input, input[type="number"]');
                if (qty) qty.value = 1;
            });

        // Clear our keys if someone wrote them anyway
        try {
            BLOCKED_KEYS.forEach(k => localStorage.removeItem(k));
        } catch (e) {}
    }

    // === PRESELECT DEFAULTS ===
    function preselectDefaults() {
        const wanted = new Set(DEFAULT_ITEMS.map(s => (s || '').trim().toLowerCase()));

        function getNameFromCheckbox(cb) {
            let nm = (cb.dataset && cb.dataset.name) ? cb.dataset.name : '';
            if (nm) return nm;
            const row = cb.closest('.menu-line, .d-flex, .form-check, .o_catering_line, .card, .list-group-item') || cb.parentElement;
            if (row) {
                const lab = row.querySelector('label, .menu-item-label, .form-check-label');
                if (lab && lab.textContent) return lab.textContent;
                if (row.textContent) return row.textContent;
            }
            return '';
        }

        const cbs = document.querySelectorAll(
            'input.menu-item[type="checkbox"], input[type="checkbox"].menu-item, input[type="checkbox"][data-name], .catering-card input[type="checkbox"]'
        );
        cbs.forEach(function (cb) {
            const nm = getNameFromCheckbox(cb).trim().toLowerCase();
            if (wanted.has(nm)) {
                cb.checked = true;
                const row = cb.closest('.menu-line, .d-flex, .form-check, .o_catering_line, .card, .list-group-item');
                const qty = row && row.querySelector('.qty-input, input[type="number"]');
                if (qty && (!qty.value || parseInt(qty.value) < 1)) {
                    qty.value = 1;
                }
            } else {
                cb.checked = false; // ensure only defaults stay checked
            }
        });

        // Trigger change so summary/total update
        const evt = new Event('change', { bubbles: true });
        document.querySelectorAll('.menu-item, .qty-input, input[type="number"]').forEach(function (el) {
            el.dispatchEvent(evt);
        });
    }

    // Debounced re-enforce to handle late DOM changes by other scripts
    let enforceTimer = null;
    function enforceDefaults() {
        if (enforceTimer) clearTimeout(enforceTimer);
        enforceTimer = setTimeout(function () {
            resetSelections();
            preselectDefaults();
        }, 0);
    }

    window.addItem = function () {
        const itemName = document.getElementById('itemName').value.trim();
        const itemPrice = document.getElementById('itemPrice').value.trim();
        const itemCategory = document.getElementById('itemCategory').value.trim();

        if (itemName && itemPrice && itemCategory) {
            selectedItems.push({
                name: itemName,
                price: parseFloat(itemPrice),
                category: itemCategory
            });
            saveItems();
            renderItems();

            document.getElementById('itemName').value = '';
            document.getElementById('itemPrice').value = '';
            document.getElementById('itemCategory').value = '';
        }
    };

    // Observe DOM changes under the catering area and re-apply defaults if needed
    function startObserver() {
        const target = document.getElementById('wrapwrap') || document.body;
        const mo = new MutationObserver(function () {
            // whenever nodes/attributes change, re-enforce defaults quickly
            enforceDefaults();
        });
        mo.observe(target, { childList: true, subtree: true, attributes: true, attributeFilter: ['checked'] });
    }

    // On catering page load
    document.addEventListener('DOMContentLoaded', function () {
        blockLocalStorageRestore(); // stop restores at the source
        enforceDefaults();          // set only defaults now
        startObserver();            // keep it enforced if anything changes later
    });

    window.addEventListener('load', function () {
        // after everything finished loading, enforce once more
        enforceDefaults();
    });
});

// Ensure each item has qty and price when saving
function normalizeAndSaveItems(data) {
    var items = {welcome:[],starter:[],main:[],biryani:[],dessert:[],leaf:[]};
    Object.keys(data || {}).forEach(function(cat){
        (data[cat]||[]).forEach(function(it){
            var obj = {id: it.id, name: it.name, price: parseFloat(it.price||0), qty: parseInt(it.qty||1)};
            items[cat].push(obj);
        });
    });
    var total = 0;
    Object.keys(items).forEach(function(cat){
        (items[cat]||[]).forEach(function(it){ total += (it.price * it.qty); });
    });
    try { localStorage.setItem('cateringData', JSON.stringify({items: items, total: total})); } catch(e){}
}
