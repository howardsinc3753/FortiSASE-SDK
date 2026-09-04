# AI SKILL — READ FIRST: MACD in the BOR Config-Generator

**If you are an AI (or engineer) about to Move / Add / Change / Delete anything in this
provisioning framework, read this first.** It tells you where things live, the one rule
that keeps it consistent, the exact MACD steps, and the invariants you must not break.

---

## Mental model — schema-first
`schema/variables.yaml` is the **single source of truth**. It drives **two** things:
1. **Config rendering** — `generator.py` resolves derived values + the platform port-map,
   then renders `templates/{bor,bor-spa}.conf.j2` in FortiOS dependency order → `.conf`.
2. **The SE form** — the future Streamlit UI walks the same YAML (scope groups, `show_if`,
   validation).

```
schema/variables.yaml ──► generator.py ──► templates/*.conf.j2 ──► generated/*.conf
        (edit here first)     (derive/render)      (dependency order)
```

### THE GOLDEN RULE
> Change the **schema first**, then the **template**, then **verify with round-trip.**
> Never hard-code in a template what should be a variable. One source of truth.

---

## File map
| File | What |
|---|---|
| `schema/variables.yaml` | variables, `pops`, `platforms`, `features`, `meta.emit_order` — **edit here first** |
| `templates/bor.conf.j2` | BOR Node template (dependency-ordered) |
| `templates/bor-spa.conf.j2` | BOR + SPA Hub template |
| `generator.py` | load schema → resolve derived → render → `--roundtrip` / `--values` |
| `app.py` | Streamlit UI — schema-driven SE form → generate → download |
| `generated/*.rendered.conf` | outputs (site-1 BOR, site-5 hub, 50G) |

Pipeline: `schema/variables.yaml → app.py (form) → generator.py → templates/*.j2 → .conf`.
Phases 0-3 done (schema, templates, generator, UI); Phase 4 = FortiManager/FortiZTP push.

---

## Run the generator (full-path commands · Windows / PowerShell)
```powershell
# 1. go to the project + install deps (once)
cd "FortiSASE-SDK\automation\sdwan-ztp\config-generator"
pip install -r requirements.txt

# 2. headless — render the 3 known sites into generated/
python "FortiSASE-SDK\automation\sdwan-ztp\config-generator\generator.py" --roundtrip

# 3. headless — render ONE site from a values file to the screen
python "FortiSASE-SDK\automation\sdwan-ztp\config-generator\generator.py" --values "C:\path\to\site.yaml"

# 4. the SE web form  ->  http://localhost:8501
streamlit run "FortiSASE-SDK\automation\sdwan-ztp\config-generator\app.py"
```
`generator.py` / `app.py` resolve the schema + templates by their own file location, so the
absolute-path forms above work from **any** current directory.

---

## MACD — the four operations

### ➕ ADD a variable
1. Add an entry under `variables:` — `key, label, group, scope, type` + (`required`/`default`,
   `roles`, `help`, `validate`, `show_if`).
2. Reference it in the template(s): `{{ key }}` or `{% if key %}…{% endif %}`.
3. If it's **derived** (computed, not typed), add the math to `build_context()` in
   `generator.py` and set `scope: derived` — do **not** add it to the form.
4. **Verify:** `python generator.py --roundtrip`.

### ✏️ CHANGE a variable
- Edit its schema entry (label / default / validate / help). Changing **scope** (tenant↔site)
  only moves *where it's entered*. Touch the template only if the rendered value/format changes.
- Verify round-trip.

### ↕️ MOVE a variable
- **In the form:** change `group` (the section it appears in) — no template change.
- **Tenant ↔ site:** change `scope` — no template change.
- **In the config output:** move the `{{ }}` in the template — but respect `emit_order` (below).

### ➖ DELETE a variable
- Remove the schema entry **and** every `{{ key }}` / `{% if key %}` in the templates **and**
  any `build_context()` derivation.
- Verify: round-trip must render with no `UndefinedError` and no leftover literal `{{ }}`.

### 🧩 ADD / CHANGE a config SECTION
- Add any new vars to the schema **first**.
- Insert the section in the template **in dependency order** (see `emit_order`).
- Verify.

### 🌐 ADD a PoP / platform / feature
- **PoP:** add a block under `pops:` (`name/fqdn/bor_node/community`). Templates iterate it —
  no template edit needed.
- **Platform:** add under `platforms:` (`wan_port`/`lan_port`). Fill real port names.
- **Feature:** add under `features:` (with `default`), then wrap the template block in
  `{% if feature %}`.

### 📶 Traffic shaper (per-site bandwidth cap) — it's just a variable
There is **no** hand-editing of the shaper block in the template. The per-site cap is driven
entirely by two schema vars, so shaper MACD = ordinary variable MACD:
- **Change a cap:** set `site_bandwidth_mbps` (upload) and/or `site_bandwidth_down_mbps`
  (advanced; `0` = match upload). Regenerate. The `{N}_MBPS_UP` / `{N}_MBPS_DOWN` shaper
  objects re-render; the shaping-policy (`dstintf "SDWAN_ZONE"`) never changes.
- **Add / Delete shaping:** `site_bandwidth_mbps > 0` emits the block; `0` = uncapped (no block).
- Both roles reference the **same `SDWAN_ZONE`** (on-ramps only; underlay is `Underlay_ZONE`),
  so one pattern covers BOR and hub and auto-covers any PoP added later.

**Live-box tweak (no regenerate)** — a shared shaper is one token bucket = aggregate cap across
both on-ramps; the shaping-policy references shapers **by name**:
```
config firewall shaper traffic-shaper
    edit "100_MBPS_UP"
        set maximum-bandwidth 200000      # 100 -> 200 Mbps (kbps units)
    next
end
```
Changing `maximum-bandwidth` on the object is safe. If you **rename or delete** a shaper object
you MUST update the `firewall shaping-policy` `traffic-shaper` / `traffic-shaper-reverse`
reference too, or the policy points at a missing shaper.

---

## 🚫 INVARIANTS — do not break these
1. **FortiOS dependency order** (`meta.emit_order`):
   `PHYSICAL interfaces → ipsec phase1 (CREATES tunnels) → phase2 → [hub: SASE_Hub IP tweak]
   → firewall address → static → communities (prefix-list/route-map) → BGP (references the
   route-maps) → SD-WAN base (zones/members/health) → firewall policy → SD-WAN service RULES
   LAST.` **A tunnel / route-map / zone must exist before anything references it.** Wrong order
   = the config fails on paste.
2. **Secrets** (`admin_password`, `seed_psk`, `fabric_psk`): `scope: secret`, `inject_at_deploy`.
   POC bakes literals; the productized path injects at deploy — keep the schema honest.
3. **Derived** values (`lan_subnet`, fabric pool, port-map, advertised-net ip/mask): computed in
   `generator.py`, never prompted.
4. **Green-field prep** stays FIRST: hardware deletes the default `lan` virtual-switch + purges
   default firewall policies (`green_field` toggle); VMs skip the switch step.

---

## ✅ VERIFY loop (run after EVERY change)
```
python generator.py --roundtrip
```
Renders site-1 (BOR vm), site-5 (BOR+SPA vm), 50G (BOR hw) → `generated/*.rendered.conf`.
Eyeball / diff against the golden `../Finalized-Template/*.conf` for completeness. **This is
the acceptance gate.** For one site: `python generator.py --values site.yaml`.

---

## FortiOS gotchas (hard-won — don't relearn them)
- **Tunnels are created by `ipsec phase1`.** Never define them in `config system interface` first.
- **Hardware LAN ports live in a `lan` virtual-switch** after factory reset — delete it before
  setting a LAN IP (VMs use `port1/port2`, no switch).
- **Jumbo MTU 9001 = VM (AWS) only**; hardware defaults to 1500.
- **BGP holdtime negotiates to `min(local, peer)`** — the *spoke* side alone shrinks failover
  (`keepalive 2 / holdtime 6` → ~6s). It does **not** need to match the FortiSASE BOR.
- **Communities must survive the FortiSASE fabric** to reach the hub — verify with
  `get router info bgp network <lan>/24` (look for the `Community:` line).
- **SD-WAN member numbering is per-device** — confirm with `diagnose sys sdwan member` before
  wiring anything to a member index.
- **SD-WAN service rule `set gateway/default enable` breaks the path** — a service rule with
  `default enable` injects a competing default that hijacks the on-ramp path (broke spoke-2 live).
  The floating static default (`router static` edit 1, distance 20) owns the fallback. Never
  enable them on `Underlay_fallback`.
- **SD-WAN health-check `members` must be EXPLICIT** — unspecified/`0` = all members, and the
  service rule won't steer on the hub fabric (broke live). Keep the health-check `members` ==
  the service `priority-members` (the on-ramps). Templates already emit `set members 1 2`.
