"""
DWG Prognostic Discussion Chart Generator
Fetches the latest CPC 6-10/8-14 day discussion and generates the styled HTML chart.
Tries multiple sources in case one is unavailable.
"""

import os
import sys
import requests
import anthropic
from datetime import datetime

HEADERS = {"User-Agent": "DWG-Weather-Chart/1.0 (Delaware Weather Group; bdiddydog@github)"}

def fetch_cpc_discussion():
    """Try multiple methods to get the CPC discussion text."""

    # ── Method 1: NWS API path-based endpoint ──────────────────────────────
    try:
        print("Trying NWS API (path endpoint)...")
        r = requests.get(
            "https://api.weather.gov/products/types/PMD/locations/KWBC",
            headers=HEADERS, timeout=20
        )
        r.raise_for_status()
        products = r.json().get("@graph", [])
        if products:
            pid = products[0]["id"]
            detail = requests.get(f"https://api.weather.gov/products/{pid}", headers=HEADERS, timeout=20)
            detail.raise_for_status()
            text = detail.json().get("productText", "")
            if text and "6-10" in text:
                print(f"  ✅ Got {len(text)} chars via Method 1")
                return text
    except Exception as e:
        print(f"  Method 1 failed: {e}")

    # ── Method 2: NWS API query-param endpoint ─────────────────────────────
    try:
        print("Trying NWS API (query params)...")
        r = requests.get(
            "https://api.weather.gov/products",
            params={"type": "PMD", "location": "KWBC", "limit": 5},
            headers=HEADERS, timeout=20
        )
        r.raise_for_status()
        products = r.json().get("@graph", [])
        if products:
            pid = products[0]["id"]
            detail = requests.get(f"https://api.weather.gov/products/{pid}", headers=HEADERS, timeout=20)
            detail.raise_for_status()
            text = detail.json().get("productText", "")
            if text and "6-10" in text:
                print(f"  ✅ Got {len(text)} chars via Method 2")
                return text
    except Exception as e:
        print(f"  Method 2 failed: {e}")

    # ── Method 3: NWS text product viewer (PMDMRD) ─────────────────────────
    try:
        print("Trying NWS text product viewer...")
        r = requests.get(
            "https://forecast.weather.gov/product.php",
            params={"site": "CPC", "issuedby": "CPC", "product": "PMD",
                    "format": "TXT", "version": "1", "glossary": "0"},
            headers=HEADERS, timeout=20
        )
        r.raise_for_status()
        # Extract text between <pre> tags
        html = r.text
        start = html.find("<pre>")
        end = html.find("</pre>")
        if start != -1 and end != -1:
            text = html[start+5:end].strip()
            if text and "6-10" in text:
                print(f"  ✅ Got {len(text)} chars via Method 3")
                return text
    except Exception as e:
        print(f"  Method 3 failed: {e}")

    # ── Method 4: CPC website directly ────────────────────────────────────
    try:
        print("Trying CPC website directly...")
        r = requests.get(
            "https://www.cpc.ncep.noaa.gov/products/predictions/610day/fxus06.html",
            headers=HEADERS, timeout=20
        )
        r.raise_for_status()
        html = r.text
        # Find the discussion text - it's usually in a <pre> block
        start = html.find("<pre>")
        end = html.find("</pre>")
        if start != -1 and end != -1:
            text = html[start+5:end].strip()
            if text and len(text) > 500:
                print(f"  ✅ Got {len(text)} chars via Method 4")
                return text
    except Exception as e:
        print(f"  Method 4 failed: {e}")

    raise RuntimeError("All fetch methods failed. Could not retrieve CPC discussion.")


# ─── CLAUDE PROMPT ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a weather data visualization expert for the Delaware Weather Group (DWG).
Convert a raw NWS CPC 6-10/8-14 day prognostic discussion into a polished dark-themed HTML dashboard.

DESIGN: Dark control-room aesthetic. Use these CSS variables:
--bg:#050c18  --panel:#070f1e  --border:#0e2844  --text:#cce4f8
--b:#00c8ff  --g:#00ff9d  --a:#ffb700  --r:#ff3c5a  --p:#b060ff  --w:#fff5e0
--warm:#ff7d3b  --cool:#5bc8ff  --wet:#38d47a  --dry:#c8941a  --dim:#2e4d6a

FONTS (Google Fonts): Orbitron (headers), Share Tech Mono (data/numbers), Barlow (body)
Add scanline overlay (body::before) and subtle grid background (body::after).
Use fadeUp animations on all cards.

REQUIRED SECTIONS:
1. MASTHEAD - Logo bug (🌩 cyan gradient box), DWG Virtual Weather Lab title, issued time,
   forecaster, source (NWS CPC College Park MD), valid dates.

2. FORECAST CONFIDENCE - Two cards side by side. Dot-pip gauges (filled circles out of 5).
   6-10 day in blue (#00c8ff), 8-14 day in amber (#ffb700).
   Show score, label (Above Average / About Average / Below Average), reason from text.

3. DIVIDER CHIP - "6-10 DAY OUTLOOK · [dates]" glowing pill in cyan.

4. 500-hPa PATTERN OVERVIEW 6-10 DAY - 3-column card grid.
   ridge cards (warm #ff7d3b top border), trough cards (cool #5bc8ff top border), neutral (green).
   Show feature name, description, anomaly values from text.

5. KEY HIGHLIGHTS 6-10 DAY - 4 big-number callout cards (hot/cold/wet/dry).
   Show region, probability %, brief reason.

6. TEMP & PRECIP BARS 6-10 DAY - Two side-by-side panels with horizontal probability bars.
   above-normal=warm/green color, below-normal=cool/dry color. Width = probability %.

7. MODEL BLEND 6-10 DAY - Horizontal bar chart. CNENS=green, ECENS=purple, GEFS=cyan,
   ECMWF=amber, GFS=orange. Show exact percentages from discussion.

8. DIVIDER CHIP - "8-14 DAY OUTLOOK · [dates]" glowing pill in purple.

9. PATTERN EVOLUTION 8-14 DAY - 3-column cards showing changes from week 1.
   Use directional emojis. Note model disagreements and preferred solution.

10. KEY HIGHLIGHTS 8-14 DAY - Same as #5 for week 2.

11. TEMP & PRECIP BARS 8-14 DAY - Same as #6 for week 2.

12. MODEL BLEND 8-14 DAY - Same as #7 for week 2 percentages.

13. MID-ATLANTIC/NE STATE TABLE - Columns: State | 6-10 Temp | 6-10 Precip | 8-14 Temp | 8-14 Precip | Note
    Pull exact A/N/B values from the state tables in the discussion.
    DELAWARE row highlighted in cyan with ⭐. Also include: Maryland, New Jersey, Pennsylvania,
    New York, Virginia, West Virginia, Ohio, Connecticut, Rhode Island.
    Use colored badge tags for A/N/B values.

14. PATTERN ANALOGS - Two side-by-side cards. 5-day (D-3) and 7-day (D-4) analog dates.
    Format: "Mon DD, YYYY".

15. FOOTER - Left: DWG branding. Right: 1991-2020 normals, next outlook date, CPC source.

OUTPUT: Complete HTML only. No markdown. No explanation. Start with <!DOCTYPE html>.
All CSS in a single <style> block. Fully self-contained."""


def generate_chart(discussion_text: str) -> str:
    print("Calling Claude API to generate chart...")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Generate the DWG chart HTML from this CPC discussion:\n\n{discussion_text}"
        }],
    )

    html = message.content[0].text.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1]
        if "```" in html:
            html = html.rsplit("```", 1)[0]

    print(f"  ✅ Generated {len(html)} chars of HTML")
    return html


def main():
    try:
        discussion = fetch_cpc_discussion()
        html = generate_chart(discussion)

        with open("dwg_prog_discussion_chart.html", "w", encoding="utf-8") as f:
            f.write(html)

        print(f"\n✅ Chart saved — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
