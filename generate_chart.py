"""
DWG Prognostic Discussion Chart Generator
Fetches the latest CPC 6-10 / 8-14 day discussion from the NWS API
and uses Claude to generate the styled HTML chart.
"""

import os
import sys
import requests
import anthropic
from datetime import datetime

# ─── 1. FETCH LATEST CPC DISCUSSION FROM NWS ───────────────────────────────

NWS_PRODUCTS_URL = "https://api.weather.gov/products"
NWS_HEADERS = {"User-Agent": "DWG-Weather-Chart/1.0 (Delaware Weather Group)"}

def fetch_cpc_discussion():
    """Fetch the latest PMDMRD product (CPC 6-10/8-14 day prog discussion)."""
    print("Fetching latest CPC discussion from api.weather.gov...")

    # Get list of latest PMD products from CPC (KWBC = College Park)
    resp = requests.get(
        NWS_PRODUCTS_URL,
        params={"type": "PMD", "location": "KWBC"},
        headers=NWS_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    products = resp.json().get("@graph", [])

    if not products:
        raise RuntimeError("No CPC PMD products found from NWS API.")

    # The first item is the most recent
    latest_id = products[0]["id"]
    print(f"  Found product ID: {latest_id}")

    # Fetch the full text of that product
    detail = requests.get(
        f"{NWS_PRODUCTS_URL}/{latest_id}",
        headers=NWS_HEADERS,
        timeout=30,
    )
    detail.raise_for_status()
    text = detail.json().get("productText", "")

    if not text:
        raise RuntimeError("CPC discussion text was empty.")

    print(f"  Fetched {len(text)} characters of discussion text.")
    return text


# ─── 2. GENERATE HTML CHART VIA CLAUDE ─────────────────────────────────────

SYSTEM_PROMPT = """You are a weather data visualization expert for the Delaware Weather Group (DWG).
Your job is to convert a raw NWS CPC 6-10 / 8-14 day prognostic discussion into a
polished, dark-themed HTML dashboard called the "DWG Virtual Weather Lab Prognostic Chart."

DESIGN RULES — follow these exactly:
- Dark control-room / radar-ops aesthetic
- CSS variables: --bg:#050c18, --panel:#070f1e, --border:#0e2844
- Accent colors: --b:#00c8ff (blue), --g:#00ff9d (green), --a:#ffb700 (amber),
  --r:#ff3c5a (red), --p:#b060ff (purple), --w:#fff5e0 (warm white)
- Temperature colors: --warm:#ff7d3b (above), --cool:#5bc8ff (below)
- Precipitation colors: --wet:#38d47a (above), --dry:#c8941a (below)
- Fonts (load from Google Fonts): Orbitron (headers/labels), Share Tech Mono (data/numbers), Barlow (body text)
- Scanline overlay via body::before
- Subtle grid background via body::after
- Fade-up animations on cards

REQUIRED SECTIONS (in this order):

1. MASTHEAD — DWG Virtual Weather Lab logo bug (🌩 emoji, cyan gradient box), title, issued time,
   forecaster name, source (NWS CPC College Park MD), valid period.

2. FORECAST CONFIDENCE — Two side-by-side cards with dot-pip gauges (filled circles = score out of 5).
   6-10 day in blue, 8-14 day in amber. Show the score, label (Above Average / About Average / etc),
   and the reason given in the discussion.

3. PERIOD DIVIDER — Glowing pill chip: "6–10 DAY OUTLOOK · [dates]" in cyan.

4. 500-hPa PATTERN OVERVIEW (6-10 DAY) — 3-column grid of feature cards.
   Each card: ridge class (warm top border) or trough class (cool top border) or neutral (green).
   Include: feature name, description, key anomaly values.
   Extract ALL major features mentioned: ridges, troughs, surface lows, frontal systems.

5. KEY PROBABILITY HIGHLIGHTS (6-10 DAY) — 4-column grid of big-number callout cards.
   hot/cold/wet/dry classes. Show region, percentage, brief description.

6. TEMPERATURE & PRECIPITATION BARS (6-10 DAY) — Two side-by-side panels.
   Horizontal bar charts for each region mentioned. Color-coded warm/cool/wet/dry.
   Bar width should be proportional to probability (e.g. 80% → width:80%).

7. MODEL BLEND WEIGHTS (6-10 DAY) — Bar chart showing each model's weight percentage.
   Use colors: CNENS=green, ECENS=purple, GEFS=cyan, ECMWF=amber, GFS=orange.

8. PERIOD DIVIDER — Glowing pill chip: "8–14 DAY OUTLOOK · [dates]" in purple.

9. PATTERN EVOLUTION (8-14 DAY) — 3-column grid showing how the pattern CHANGES from week 1.
   Use directional emojis (↖️ ➡️ ⬆️ etc). Note model disagreements and preferred solution.

10. KEY PROBABILITY HIGHLIGHTS (8-14 DAY) — Same format as #5 but for week 2.

11. TEMPERATURE & PRECIPITATION BARS (8-14 DAY) — Same format as #6 but for week 2.

12. MODEL BLEND WEIGHTS (8-14 DAY) — Same format as #7 but for week 2 blend.

13. MID-ATLANTIC & NORTHEAST STATE TABLE — HTML table with columns:
    State | 6-10 Temp | 6-10 Precip | 8-14 Temp | 8-14 Precip | Note
    Highlight DELAWARE row with a ⭐ and cyan color.
    Include: Delaware, Maryland, New Jersey, Pennsylvania, New York,
    Virginia, West Virginia, Ohio, Connecticut, Rhode Island.
    Use colored tag badges (tag-above-t, tag-below-t, tag-near-t, tag-above-p, tag-below-p, tag-near-p).

14. PATTERN ANALOGS — Two side-by-side cards showing 5-day (D-3) and 7-day (D-4) analog dates.
    Format dates as "Month DD, YYYY" (e.g. "Mar 21, 2007").

15. FOOTER — Left: DWG branding. Right: base period, next outlook date if mentioned, source.

OUTPUT: Return ONLY the complete HTML document, nothing else. No markdown fences, no explanation.
The HTML must be self-contained (all CSS inline in <style> tag). Start with <!DOCTYPE html>.
"""

def generate_chart(discussion_text: str) -> str:
    """Send discussion text to Claude and get back the HTML chart."""
    print("Sending to Claude API to generate chart...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Here is the latest CPC prognostic discussion. Generate the DWG chart HTML:\n\n{discussion_text}",
            }
        ],
    )

    html = message.content[0].text.strip()

    # Strip markdown fences if Claude accidentally adds them
    if html.startswith("```"):
        html = html.split("\n", 1)[1]
        if html.endswith("```"):
            html = html.rsplit("```", 1)[0]

    print(f"  Generated {len(html)} characters of HTML.")
    return html


# ─── 3. SAVE OUTPUT ─────────────────────────────────────────────────────────

OUTPUT_FILE = "dwg_prog_discussion_chart.html"

def main():
    try:
        discussion = fetch_cpc_discussion()
        html = generate_chart(discussion)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"\n✅ Chart saved to {OUTPUT_FILE}")
        print(f"   Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
