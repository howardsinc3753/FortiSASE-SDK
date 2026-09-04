# Send-Communities · BETA — SLA-driven preemptive failover

**Upgrade** of the static `Send-Communities/` baseline. Adds sub-5s return-path failover
by **preempting the stale route** instead of waiting for it to be withdrawn.

> 🧪 **BETA — lab-validate the two gates below before production.** The baseline
> (`../Send-Communities/`) stays as the proven fallback.

## The problem it solves
On a Dallas **hard-down**, the Dallas BGP session is gone — the spoke can't announce its
own death. The **Dallas BOR node** (FortiSASE side, *not yours to tune*) holds the stale
`10.200.x0.0/24 :10 / LP200` for its **holdtime (~45s)**. Miami at LP100 loses to a dead
route for that whole window. Removing graceful-restart did **not** help → confirms it's
holdtime-driven route retention, which you cannot shorten on the BOR side.

## The fix: preempt, don't wait
Bind **both** spoke BGP neighbors' SD-WAN entries to the **Dallas** member. Now Miami's
`route-map-out-preferable` flips on **Dallas's** health, evaluated locally on the healthy
Miami session. When Dallas fails, Miami advertises a community that maps to **LP250 at the
hub — above** Dallas's stale 200 — so the hub moves *before* the withdrawal ever happens.

> Inversion vs the Fortinet KB: the KB has each neighbor signalling its **own** health.
> Here the **surviving** neighbor signals the **other's** health. Same knob, different wiring.
> Note the map roles invert on Miami: `route-map-out` = the *failure* (promote) map,
> `route-map-out-preferable` = the *normal* (standby) map.

## Four-community scheme
| Community | Meaning | Hub Local-Pref |
|---|---|---|
| `65001:15` | **Miami promoted** (Dallas out-of-SLA / down) | **250** ← preempts stale Dallas |
| `65001:10` | Dallas active (healthy) | 200 |
| `65001:20` | Miami standby | 100 |
| `65001:30` | Dallas degraded (brownout, session still up) | 50 |

### State walk
- **Both healthy** — Dallas `:10`/200 wins, Miami `:20`/100 standby. No ECMP.
- **Dallas brownout** (session up) — Dallas sends `:30`/50, Miami sends `:15`/250. Double-signalled → Miami wins.
- **Dallas hard-down** — Dallas session gone, stale `:10`/200 lingers at hub; Miami sends `:15`/250 and **preempts** it. *This is the 45s case.*
- **Recovery** — `recoverytime` damps the flap, then back to 200/100.

## 🔴 Two lab gates — must pass before trusting in prod
1. **Non-egress member binding.** Can a BGP neighbor's SD-WAN member be a member that is
   NOT its egress? (Miami neighbor → Dallas member.) Verify: `diagnose sys sdwan neighbor`.
2. **Dead member = out-of-SLA?** The hard-down case rests entirely on this. Pull the Dallas
   tunnel and confirm the promote fires:
   ```
   diagnose sys sdwan health-check status HC_SPA_HUB   # Seq(<dallas>): state(dead)
   get router info bgp neighbors 172.16.0.1 advertised-routes   # 10.200.x0.0/24 out Miami with 65001:15
   ```
   If FortiOS freezes last-known SLA on a dead member, the promote never fires → we need a
   different trigger (fallback: `set member <dal> <mia>` + `minimum-sla-meet-members 2`, but
   Miami then self-promotes while broken — less clean).

## ⚠️ Member numbering — VERIFY YOURS
The whole design binds to the **Dallas** member. Scripts show it as **member 3** (per your
config), but confirm with `diagnose sys sdwan member` and substitute your real ID. Wrong ID
= trigger wired to the wrong link, silently never fires.

## Also do (independent wins)
- **Spoke holdtime** (yours to change): `keepalive-timer 5 / holdtime-timer 15` — negotiates
  the session to 15s regardless of the BOR. Shrinks the stale window; free.
- **Forward path**: point the hub-bound SD-WAN service rule at `HC_SPA_HUB`, and add
  `10.30.1.0/24` to its dst (the loopbacks are currently ECMP / forward-asymmetric).

## Expected timing
Detection ~2.5s (500ms × failtime 5) + advertise ~1s + hub best-path recompute (event-driven)
≈ **3–4s vs 45s**.

## Files
- `spoke-1_dynamic-failover_BETA.md` — LAN `10.200.10.0/24`
- `spoke-2_dynamic-failover_BETA.md` — LAN `10.200.20.0/24`
- `hub-1_dynamic-failover_BETA.md` — extend `RM_FABRIC_IN` with `:15`/250 and `:30`/50
