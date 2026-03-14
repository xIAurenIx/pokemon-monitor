import requests
import os
from datetime import datetime


WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# Colour codes (Discord uses decimal integers for embed colours)
COLOURS = {
    "new_sale": 0x747F8D,   # grey
    "spike":    0xED4245,   # red
    "dip":      0x3BA55D,   # green
    "ath":      0xFAA61A,   # gold
    "atl":      0xFAA61A,   # gold
}

EMOJIS = {
    "new_sale": "📦",
    "spike":    "🔥",
    "dip":      "💰",
    "ath":      "⭐",
    "atl":      "⬇️",
}

TITLES = {
    "new_sale": "New sale detected",
    "spike":    "Price spike",
    "dip":      "Price dip — potential buy",
    "ath":      "New all-time high",
    "atl":      "New all-time low",
}


def send_alert(alert: dict):
    """Posts a formatted Discord embed for a price alert."""
    alert_type  = alert["type"]
    product     = alert["product"]
    transaction = alert["transaction"]
    new_price   = alert["new_price"]
    avg_price   = alert["avg_price"]
    pct_change  = alert["pct_change"]

    emoji = EMOJIS[alert_type]
    title = TITLES[alert_type]
    colour = COLOURS[alert_type]

    # Build fields
    fields = [
        {"name": "Sale price", "value": f"£{new_price:.2f}", "inline": True},
        {"name": "Marketplace", "value": transaction.marketplace.capitalize(), "inline": True},
    ]

    if avg_price:
        direction = "+" if pct_change >= 0 else ""
        fields.append({"name": "30-day avg", "value": f"£{avg_price:.2f}", "inline": True})
        fields.append({"name": "vs avg", "value": f"{direction}{pct_change}%", "inline": True})

    # Portfolio P&L if user holds this product
    if product.units_held and product.units_held > 0 and product.purchase_price_gbp:
        cost        = product.purchase_price_gbp
        gain_per    = new_price - cost
        gain_total  = gain_per * product.units_held
        pct_vs_cost = ((new_price - cost) / cost) * 100
        direction   = "+" if gain_per >= 0 else ""
        fields.append({
            "name": f"Your {product.units_held} unit(s)",
            "value": (
                f"Cost: £{cost:.2f} · Now: £{new_price:.2f}\n"
                f"P&L: {direction}£{gain_total:.2f} ({direction}{pct_vs_cost:.1f}%)"
            ),
            "inline": False,
        })

    embed = {
        "title": f"{emoji}  {title}",
        "description": f"**{product.product_name}**",
        "color": colour,
        "fields": fields,
        "footer": {"text": f"Pokemon Monitor · {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC"},
        "url": transaction.url or "",
    }

    payload = {"embeds": [embed]}
    response = requests.post(WEBHOOK_URL, json=payload, timeout=10)

    if response.status_code == 204:
        print(f"[Discord] Alert sent: {title} — {product.product_name}")
    else:
        print(f"[Discord] Failed ({response.status_code}): {response.text}")
