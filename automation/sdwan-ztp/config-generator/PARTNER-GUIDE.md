# FortiSASE Branch On-Ramp — Config Builder
### Partner Quick-Start Guide

This tool builds a **ready-to-deploy FortiGate config** for a branch site (BOR Node) or a
hub (BOR + SPA Hub). You fill in a short form, click a button, and download a `.conf` file.
**No FortiOS command-line knowledge required.**

---

## 1. One-time setup (do this once per computer)

You need **Python** installed. Check by opening **PowerShell** and typing:

```powershell
python --version
```

If you see a version number (e.g. `Python 3.13`), you're good. If not, install it from
<https://www.python.org/downloads/> (tick **"Add Python to PATH"** during install).

Then install the tool's requirements — copy-paste this whole block into PowerShell:

```powershell
cd FortiSASE-SDK\automation\sdwan-ztp\config-generator
pip install -r requirements.txt
```

---

## 2. Start the tool (every time you want to use it)

Copy-paste these two lines into **PowerShell**:

```powershell
cd FortiSASE-SDK\automation\sdwan-ztp\config-generator
streamlit run app.py
```

Your web browser opens automatically. If it doesn't, open a browser and go to:

> **http://localhost:8501**

Leave the PowerShell window open while you use the tool. To stop it, click that window and
press **Ctrl + C**.

---

## 3. Build a config — 5 steps

| Step | What you do |
|------|-------------|
| **1. Quick start** | At the top, type a **Site ID** (any number — 1, 2, 3 … 100), pick the **Role**, and click **⬇ Load baseline**. This fills the whole form with working example values. |
| **2. Pick role & model** | **BOR Node (spoke)** = a normal branch. **BOR + SPA Hub** = the bridge site. Choose your **FortiGate model** (VM, 30G, 50G…). |
| **3. Change what's different** | Update the boxes that are unique to this site — **hostname**, **WAN IP/gateway**, **LAN IP**, **Router-ID**. Each box shows a faint example of the format. |
| **4. (Optional) extra networks** | Under **LAN** and **Routing** you can click the **+** to add more subnets (see format below). |
| **5. Generate & download** | Click **⚙ Generate config**. If anything's missing it tells you in plain English. When it's green, click **⬇ Download .conf**. |

---

## 4. What to type in the "+" boxes

The two add-a-row boxes (**Extra LAN / VLAN networks** and **Extra trusted-host return
routes**) want a network in **CIDR** format — an address followed by a slash and a number:

| Type this | Meaning |
|-----------|---------|
| `10.7.20.0/24` | a whole subnet (256 addresses) — **the usual choice** |
| `10.8.0.0/16`  | a larger subnet |
| `198.51.100.5/32` | a single computer |
| `198.51.100.5` | (no slash) — treated as a single computer automatically |

> **Tip:** you can even paste a device's own address like `10.7.20.55/24` — the tool
> automatically snaps it to the correct subnet (`10.7.20.0`). You can't get it wrong.

---

## 5. Deploy the config you downloaded

The downloaded `.conf` is plain text, ready to paste into the FortiGate:

1. Log into the FortiGate CLI (console, or **>_ CLI Console** in the web GUI).
2. Open the `.conf` file in Notepad, **select all**, **copy**.
3. **Paste** into the CLI. The device applies it top-to-bottom in the correct order.

> The file is built in FortiOS **dependency order** on purpose — tunnels are created before
> anything uses them — so a straight top-to-bottom paste just works on a factory-reset box.

---

## Troubleshooting — "it won't run"

| What you see | Fix |
|--------------|-----|
| `streamlit : The term 'streamlit' is not recognized` | Run it as `python -m streamlit run app.py`, **or** re-run the `pip install` in Step 1. |
| `Error: File does not exist: app.py` | You're in the wrong folder. Run the `cd …\config-generator` line **first**, then `streamlit run app.py`. |
| A warning about *"missing ScriptRunContext / use `streamlit run`"* and nothing opens | You ran `python app.py`. Use **`streamlit run app.py`** instead. |
| Browser didn't open | Open one yourself and go to **http://localhost:8501**. |
| Red text after **Generate** | That's the tool checking your inputs — read the message, fix that box, click Generate again. |

---

*Questions? Contact your Fortinet SE.*
