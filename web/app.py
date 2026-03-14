import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flask import Flask, render_template_string, request, jsonify, redirect
from models.schema import get_session, Product
from datetime import datetime
import uuid
import os

app = Flask(__name__)
PASSWORD = os.environ.get("UI_PASSWORD", "pokemon123")

with app.app_context():
    try:
        from models.schema import create_tables
        create_tables()
    except Exception as e:
        print(f"DB init error: {e}")

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pokemon Monitor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #111; }
    .header { background: #fff; border-bottom: 1px solid #e5e5e5; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
    .header h1 { font-size: 16px; font-weight: 600; }
    .container { max-width: 860px; margin: 24px auto; padding: 0 16px; }
    .tabs { display: flex; gap: 0; border-bottom: 1px solid #e5e5e5; margin-bottom: 20px; }
    .tab { padding: 8px 18px; font-size: 14px; cursor: pointer; border-bottom: 2px solid transparent; color: #666; background: none; border-top: none; border-left: none; border-right: none; }
    .tab.active { color: #111; font-weight: 500; border-bottom-color: #111; }
    .card { background: #fff; border: 1px solid #e5e5e5; border-radius: 10px; padding: 20px; margin-bottom: 12px; }
    label { font-size: 12px; color: #666; display: block; margin-bottom: 4px; margin-top: 12px; }
    input, select { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .btn { padding: 9px 18px; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; border: 1px solid #ddd; background: #fff; }
    .btn-primary { background: #111; color: #fff; border-color: #111; width: 100%; margin-top: 16px; }
    .btn-primary:hover { background: #333; }
    .product-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f0f0f0; }
    .product-row:last-child { border-bottom: none; }
    .product-name { font-size: 14px; font-weight: 500; }
    .product-sub { font-size: 12px; color: #888; margin-top: 2px; }
    .badge { font-size: 11px; padding: 2px 8px; border-radius: 20px; }
    .badge-on { background: #e6f9f0; color: #2d8a5a; }
    .badge-off { background: #f5f5f5; color: #999; }
    .toggle-btn { font-size: 12px; padding: 4px 10px; border-radius: 4px; cursor: pointer; border: 1px solid #ddd; background: #fff; margin-left: 8px; }
    .delete-btn { font-size: 12px; padding: 4px 10px; border-radius: 4px; cursor: pointer; border: 1px solid #ffcccc; background: #fff; color: #cc4444; margin-left: 4px; }
    .success { background: #e6f9f0; border: 1px solid #b3e6cc; border-radius: 6px; padding: 12px; font-size: 14px; color: #2d8a5a; margin-bottom: 16px; }
    .pnl-pos { color: #2d8a5a; }
    .pnl-neg { color: #cc4444; }
    #tab-add, #tab-portfolio { display: none; }
    #tab-add.active, #tab-portfolio.active { display: block; }
  </style>
</head>
<body>

<div class="header">
  <h1>🎴 Pokemon Monitor</h1>
  <span style="font-size:13px;color:#888">Private dashboard</span>
</div>

<div class="container">

  {% if message %}
  <div class="success">{{ message }}</div>
  {% endif %}

  <div class="tabs">
    <button class="tab active" onclick="showTab('add')">Add product</button>
    <button class="tab" onclick="showTab('portfolio')">My portfolio ({{ products|length }})</button>
  </div>

  <!-- ADD TAB -->
  <div id="tab-add" class="active">
    <div class="card">
      <div style="font-size:14px;font-weight:500;margin-bottom:4px">Track a new product</div>
      <div style="font-size:13px;color:#888;margin-bottom:16px">Add a product and the bot will start monitoring it on the next run.</div>

      <form method="POST" action="/add">
        <label>Product name</label>
        <input type="text" name="product_name" placeholder="e.g. Pokemon Center ETB: Mega Evolution" required>

        <label>eBay search query</label>
        <input type="text" name="search_query" placeholder='e.g. "pokemon center etb mega evolution" sold' required>
        <div style="font-size:11px;color:#aaa;margin-top:4px">Tip: use the exact words you'd type into eBay's search bar.</div>

        <div class="grid2">
          <div>
            <label>Alert threshold</label>
            <select name="alert_threshold_percent">
              <option value="5">±5% (sensitive)</option>
              <option value="10" selected>±10% (default)</option>
              <option value="15">±15% (relaxed)</option>
              <option value="20">±20% (major moves only)</option>
            </select>
          </div>
          <div>
            <label>Category</label>
            <select name="category">
              <option value="sealed">Sealed product</option>
              <option value="graded">Graded card</option>
              <option value="single">Single card</option>
            </select>
          </div>
          <div>
            <label>Units I hold (optional)</label>
            <input type="number" name="units_held" placeholder="0" min="0">
          </div>
          <div>
            <label>My purchase price in £ (optional)</label>
            <input type="text" name="purchase_price_gbp" placeholder="e.g. 85.00">
          </div>
        </div>

        <label>Notes (optional)</label>
        <input type="text" name="notes" placeholder="e.g. bought at Pokemon Center exclusive event">

        <button type="submit" class="btn btn-primary">Start tracking →</button>
      </form>
    </div>
  </div>

  <!-- PORTFOLIO TAB -->
  <div id="tab-portfolio">
    <div class="card">
      {% if products %}
        {% for p in products %}
        <div class="product-row">
          <div style="flex:1">
            <div class="product-name">{{ p.product_name }}</div>
            <div class="product-sub">
              Threshold: ±{{ p.alert_threshold_percent|int }}%
              {% if p.units_held %}· {{ p.units_held }} unit(s) @ £{{ "%.2f"|format(p.purchase_price_gbp) }}{% endif %}
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:4px">
            <span class="badge {{ 'badge-on' if p.is_active else 'badge-off' }}">
              {{ 'Active' if p.is_active else 'Paused' }}
            </span>
            <form method="POST" action="/toggle/{{ p.product_id }}" style="display:inline">
              <button type="submit" class="toggle-btn">{{ 'Pause' if p.is_active else 'Resume' }}</button>
            </form>
            <form method="POST" action="/delete/{{ p.product_id }}" style="display:inline" onsubmit="return confirm('Remove {{ p.product_name }}?')">
              <button type="submit" class="delete-btn">Remove</button>
            </form>
          </div>
        </div>
        {% endfor %}
      {% else %}
        <div style="font-size:14px;color:#888;text-align:center;padding:20px 0">No products yet — add one above.</div>
      {% endif %}
    </div>
  </div>

</div>

<script>
function showTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', (i===0&&name==='add')||(i===1&&name==='portfolio')));
  document.getElementById('tab-add').classList.toggle('active', name === 'add');
  document.getElementById('tab-portfolio').classList.toggle('active', name === 'portfolio');
}
// If message shown, start on portfolio tab
{% if message %}showTab('portfolio');{% endif %}
</script>

</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    pw = request.args.get("pw", "")
    if pw != PASSWORD:
        return """
        <form style="max-width:300px;margin:80px auto;font-family:sans-serif">
          <p style="margin-bottom:12px;font-weight:500">Pokemon Monitor — Login</p>
          <input name="pw" type="password" placeholder="Password" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px">
          <button style="width:100%;padding:8px;background:#111;color:#fff;border:none;border-radius:4px;cursor:pointer">Enter</button>
        </form>
        """
    try:
        from models.schema import create_tables
        create_tables()
        session = get_session()
        products = session.query(Product).order_by(Product.created_at.desc()).all()
        session.close()
        return render_template_string(HTML, products=products, message=None)
    except Exception as e:
        return f"<pre style='padding:20px;color:red'>ERROR: {str(e)}</pre>", 500


@app.route("/add", methods=["POST"])
def add_product():
    session = get_session()
    product = Product(
        product_id=f"PKM{str(uuid.uuid4())[:6].upper()}",
        product_name=request.form["product_name"],
        search_query=request.form["search_query"],
        alert_threshold_percent=float(request.form.get("alert_threshold_percent", 10)),
        category=request.form.get("category", "sealed"),
        units_held=int(request.form.get("units_held") or 0),
        purchase_price_gbp=float(request.form.get("purchase_price_gbp") or 0) or None,
        notes=request.form.get("notes") or None,
    )
    session.add(product)
    session.commit()
    session.close()
    products = get_session().query(Product).order_by(Product.created_at.desc()).all()
    return render_template_string(HTML, products=products, message=f"✓ {product.product_name} is now being tracked.")


@app.route("/toggle/<product_id>", methods=["POST"])
def toggle_product(product_id):
    session = get_session()
    product = session.query(Product).filter_by(product_id=product_id).first()
    if product:
        product.is_active = not product.is_active
        session.commit()
    session.close()
    return redirect(f"/?pw={PASSWORD}#portfolio")


@app.route("/delete/<product_id>", methods=["POST"])
def delete_product(product_id):
    session = get_session()
    product = session.query(Product).filter_by(product_id=product_id).first()
    if product:
        session.delete(product)
        session.commit()
    session.close()
    return redirect(f"/?pw={PASSWORD}#portfolio")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
