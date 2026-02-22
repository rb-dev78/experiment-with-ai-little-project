// ── Product catalogue ──────────────────────────────────────────────
const PRODUCTS = [
  { id: 1,  name: 'Espresso',       emoji: '☕', price: 2.50 },
  { id: 2,  name: 'Cappuccino',     emoji: '🍵', price: 3.75 },
  { id: 3,  name: 'Croissant',      emoji: '🥐', price: 2.25 },
  { id: 4,  name: 'Bagel',          emoji: '🥯', price: 1.99 },
  { id: 5,  name: 'Orange Juice',   emoji: '🍊', price: 3.00 },
  { id: 6,  name: 'Muffin',         emoji: '🧁', price: 2.00 },
  { id: 7,  name: 'Caesar Salad',   emoji: '🥗', price: 7.50 },
  { id: 8,  name: 'Sandwich',       emoji: '🥪', price: 5.99 },
  { id: 9,  name: 'Cheesecake',     emoji: '🍰', price: 4.50 },
  { id: 10, name: 'Water Bottle',   emoji: '💧', price: 1.25 },
];

const TAX_RATE = 0.08; // 8 %

// ── State ──────────────────────────────────────────────────────────
let cart = {}; // { productId: quantity }

// ── DOM helpers ────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

function fmt(n) {
  return '$' + n.toFixed(2);
}

// ── Render products ────────────────────────────────────────────────
function renderProducts() {
  const grid = $('product-grid');
  grid.innerHTML = '';
  PRODUCTS.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', `Add ${p.name} to cart`);
    card.innerHTML = `
      <span class="emoji">${p.emoji}</span>
      <div class="name">${p.name}</div>
      <div class="price">${fmt(p.price)}</div>
    `;
    card.addEventListener('click', () => addToCart(p.id));
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        addToCart(p.id);
      }
    });
    grid.appendChild(card);
  });
}

// ── Cart operations ────────────────────────────────────────────────
function addToCart(id) {
  cart[id] = (cart[id] || 0) + 1;
  renderCart();
}

function setQty(id, qty) {
  if (qty <= 0) {
    delete cart[id];
  } else {
    cart[id] = qty;
  }
  renderCart();
}

// ── Render cart ────────────────────────────────────────────────────
function renderCart() {
  const list    = $('cart-items');
  const ids     = Object.keys(cart).map(Number);
  list.innerHTML = '';

  ids.forEach(id => {
    const p   = PRODUCTS.find(x => x.id === id);
    const qty = cart[id];
    const li  = document.createElement('li');
    li.className = 'cart-item';
    li.innerHTML = `
      <span class="ci-emoji">${p.emoji}</span>
      <div class="ci-info">
        <div class="ci-name">${p.name}</div>
        <div class="ci-unit">${fmt(p.price)} each</div>
      </div>
      <div class="qty-controls">
        <button class="qty-btn" aria-label="Decrease quantity" data-id="${id}" data-delta="-1">−</button>
        <span class="qty-display">${qty}</span>
        <button class="qty-btn" aria-label="Increase quantity" data-id="${id}" data-delta="1">+</button>
      </div>
      <span class="ci-subtotal">${fmt(p.price * qty)}</span>
    `;
    list.appendChild(li);
  });

  // Qty button events
  list.querySelectorAll('.qty-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const id    = Number(btn.dataset.id);
      const delta = Number(btn.dataset.delta);
      setQty(id, (cart[id] || 0) + delta);
    });
  });

  renderTotals(ids);
}

// ── Totals ─────────────────────────────────────────────────────────
function calcTotals() {
  const subtotal = Object.entries(cart).reduce((sum, [id, qty]) => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    return sum + p.price * qty;
  }, 0);
  const tax   = subtotal * TAX_RATE;
  const total = subtotal + tax;
  return { subtotal, tax, total };
}

function renderTotals(ids) {
  const { subtotal, tax, total } = calcTotals();
  $('subtotal').textContent = fmt(subtotal);
  $('tax').textContent      = fmt(tax);
  $('total').textContent    = fmt(total);
  $('checkout-btn').disabled = ids.length === 0;
}

// ── Checkout ───────────────────────────────────────────────────────
function checkout() {
  const { subtotal, tax, total } = calcTotals();

  // Build receipt lines
  const lines = Object.entries(cart).map(([id, qty]) => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    return `<div class="receipt-line">
      <span>${p.emoji} ${p.name} × ${qty}</span>
      <span>${fmt(p.price * qty)}</span>
    </div>`;
  }).join('');

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="receipt" role="dialog" aria-modal="true" aria-labelledby="receipt-title">
      <h2 id="receipt-title">✅ Order Complete!</h2>
      <p class="sub">Thank you for your purchase</p>
      <div class="receipt-lines">
        ${lines}
        <div class="receipt-line"><span>Tax (${(TAX_RATE * 100).toFixed(0)}%)</span><span>${fmt(tax)}</span></div>
      </div>
      <div class="receipt-total"><span>Total</span><span>${fmt(total)}</span></div>
      <button class="close-btn" id="close-receipt">New Order</button>
    </div>
  `;

  document.body.appendChild(overlay);

  $('close-receipt').addEventListener('click', () => {
    document.body.removeChild(overlay);
    cart = {};
    renderCart();
  });

  overlay.addEventListener('click', e => {
    if (e.target === overlay) {
      document.body.removeChild(overlay);
      cart = {};
      renderCart();
    }
  });
}

// ── Boot ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderProducts();
  renderCart();
  $('checkout-btn').addEventListener('click', checkout);
});
