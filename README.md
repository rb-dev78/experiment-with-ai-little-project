# QuickPOS – Point of Sale

A small, zero-dependency **Point of Sale** web app built with plain HTML, CSS, and JavaScript.

## Features

| Feature | Details |
|---|---|
| Product catalogue | 10 items (espresso, croissant, salad …) with emoji icons and prices |
| Shopping cart | Add items by clicking a product card; adjust quantity with +/− buttons |
| Live totals | Subtotal, 8 % tax, and grand total update in real time |
| Receipt modal | Full itemised receipt shown on checkout; "New Order" clears the cart |
| Responsive | Two-column layout collapses to single column on narrow screens |
| Accessible | Keyboard-navigable product cards, ARIA labels, modal role/aria-modal |

## Getting started

No build step required – just open `index.html` in any modern browser:

```bash
# Option 1 – open directly
open index.html          # macOS
xdg-open index.html      # Linux
start index.html         # Windows

# Option 2 – serve locally (avoids any file:// quirks)
npx serve .              # Node.js
python3 -m http.server   # Python
```

## File structure

```
index.html   – markup (header, product grid, cart panel)
styles.css   – all styling (grid, cards, modal, responsive breakpoints)
app.js       – product data, cart state, render functions, checkout logic
```

