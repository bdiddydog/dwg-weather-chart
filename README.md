# DWG Prognostic Chart — Automated Setup Guide

This repository automatically fetches the latest CPC 6–10 / 8–14 day forecast
discussion every 2 days and regenerates the styled DWG chart HTML.

---

## What You Need Before Starting

- A free **GitHub account** → [github.com/signup](https://github.com/signup)
- A paid **Anthropic API account** → [console.anthropic.com](https://console.anthropic.com)
  *(Claude API — a few cents per run, roughly $0.10–0.20 per chart generation)*

---

## One-Time Setup (takes about 10 minutes)

### Step 1 — Create a new GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. Name it something like `dwg-weather-chart`
3. Make it **Public** (required for free GitHub Actions)
4. Click **Create repository**

---

### Step 2 — Upload the files

You need to add these 3 files to your new repository:

| File | Where to put it |
|---|---|
| `generate_chart.py` | Root of the repo |
| `dwg_prog_discussion_chart.html` | Root of the repo (initial version) |
| `.github/workflows/update-chart.yml` | Must go in a folder called `.github/workflows/` |

**To upload files:**
1. On your repository page, click **Add file → Upload files**
2. Drag and drop `generate_chart.py` and `dwg_prog_discussion_chart.html`
3. Click **Commit changes**

**To create the workflow file** (the tricky one — you can't just upload to a subfolder easily):
1. Click **Add file → Create new file**
2. In the filename box, type: `.github/workflows/update-chart.yml`
   *(GitHub will auto-create the folders as you type the slashes)*
3. Paste the entire contents of `update-chart.yml` into the editor
4. Click **Commit changes**

---

### Step 3 — Add your Anthropic API key

This is the secret key that lets the script call Claude. Keep it private.

1. Go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Click **Create Key**, name it `DWG Chart`, copy the key (starts with `sk-ant-...`)
3. In your GitHub repo, click **Settings → Secrets and variables → Actions**
4. Click **New repository secret**
5. Name: `ANTHROPIC_API_KEY`
6. Value: paste your key
7. Click **Add secret**

---

### Step 4 — Test it manually

1. In your repo, click the **Actions** tab
2. Click **Update DWG Prognostic Chart** in the left sidebar
3. Click **Run workflow → Run workflow**
4. Watch it run (takes about 60–90 seconds)
5. When it goes green ✅, click on your repo's main page — you'll see the
   `dwg_prog_discussion_chart.html` file was updated with today's discussion!

---

## After Setup — It Runs Automatically

The workflow runs every 2 days at 5 PM ET. You don't have to do anything.

To check on it: **Actions tab → look for green checkmarks**

To run it early anytime: **Actions → Run workflow button**

---

## Using the Chart on Your Google Sites Page

GitHub can serve the raw HTML file at a public URL:

```
https://raw.githubusercontent.com/YOUR-USERNAME/dwg-weather-chart/main/dwg_prog_discussion_chart.html
```

Replace `YOUR-USERNAME` with your GitHub username.

You can embed this in Google Sites using an **Embed** block, or link to it directly.

For a nicer URL, you can also enable **GitHub Pages**:
1. Settings → Pages → Source: Deploy from branch → main → / (root)
2. Your chart will be live at: `https://YOUR-USERNAME.github.io/dwg-weather-chart/dwg_prog_discussion_chart.html`

---

## Schedule

The chart updates every **2 days at 5:00 PM Eastern** (automatically).

To change the schedule, edit `.github/workflows/update-chart.yml` and modify the cron line.
Common options:
- Every day at 5 PM ET: `0 22 * * *`
- Every 2 days at 5 PM ET: `0 22 */2 * *`
- Every 3 days at 5 PM ET: `0 22 */3 * *`

---

## Troubleshooting

**The workflow failed (red X):**
Click on the failed run → click the failed step → read the error message.
Most common causes:
- API key not added correctly → re-check Step 3
- NWS API was temporarily down → just run it again

**The chart looks wrong:**
Paste the latest discussion text directly to Claude in a chat and ask it to regenerate.

---

*DWG Virtual Weather Lab · Delaware Weather Group*
*Source: NWS Climate Prediction Center · FXUS06 KWBC / PMDMRD*
