# FortiSASE On-Ramp — Engineering Deep-Dive (the core strategy)

> **Tier 1 (official docs).** Compiled June 2026 from docs.fortinet.com. Scope: every FortiSASE on-ramp — **agent, agentless-SWG, thin-edge, Branch/SD-WAN On-Ramp (BOR), and the SPA/FortiGate-native path** — with provisioning runbooks, a master pothole catalog, and a verdict ledger. Every load-bearing claim carries a verbatim quote + source URL and a status: **CONFIRMED / PARTIALLY-CONFIRMED / UNVERIFIED**.
> **Why this doc exists:** the on-ramp is *the* FortiSASE strategy — it's how traffic gets onto the security fabric, and it's where the provisioning complexity and field potholes live. This supersedes/refines the on-ramp sections of `01-architecture-and-onramps.md` where they differ (esp. the bandwidth nuance in §3 and the FortiGate-ZTP fact in §4b).
> **Sourcing caveat:** docs.fortinet.com renders article bodies client-side; some quotes were captured from Fortinet's own indexed page text rather than a rendered fetch. Wording is consistent across version pages (high confidence), but pull the live page in a browser before putting an exact number/SKU on a customer artifact.

---

## 0. The on-ramp taxonomy — clear this up first (POTHOLE: naming)

The **same site-based feature has three names** across GUI tracks and product eras. This confuses every engineer once.

| Term | What it actually is |
|---|---|
| **On-ramp** (general) | Umbrella: how traffic gets *onto* FortiSASE — agent / agentless / site-IPsec. |
| **On-ramp tunnel** | The **Feature-track** menu for the site-based path: `Operations > Connectivity > On-ramp tunnel` (Security PoP tab). |
| **SD-WAN On-Ramp** | The **Mature-track** GUI name for the *same* feature: `Edge Devices > SD-WAN On-Ramp`. |
| **Branch On-ramp** | The **functional/prose** name ("dial into a FortiSASE Branch On-ramp location"). |
| **Branch On-Ramp (BOR)** | The **MSSP-arch-guide** name for the *node* — the special security PoP that terminates branch tunnels and acts as Hub. |
| **Thin-edge** | A **different** model: flat branch, *no local FortiGate*, using FortiAP/FortiExtender with L2 encapsulation, managed directly by FortiSASE. **Not** BOR. |

> "You can configure a certified IPsec device for **Branch On-ramp** by setting up an IPsec tunnel between the certified IPsec device located at the branch and a FortiSASE Branch On-ramp location." — page titled *SD-WAN On-Ramp* ([Mature 213023](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp)) — **CONFIRMED** (proves SD-WAN On-Ramp == Branch On-ramp).
> "Thin branches can be equipped with FortiAPs or FortiExtenders (called ThinEdge devices)… Two communication channels are established… a control channel… and a data channel used to steer ThinEdge traffic to FortiSASE with **Layer-2 encapsulation**." — [MSSP Arch Guide, Thin Edge](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/829351/thin-edge) — **CONFIRMED** (proves thin-edge ≠ BOR).

⚠ **Pothole N1:** A Mature-era runbook says `Edge Devices > SD-WAN On-Ramp`; a Feature-track tenant shows `Operations > Connectivity > On-ramp tunnel`. Same feature — don't think you're missing a license.
⚠ **Pothole N2:** "Branch On-ramp" (site IPsec, FortiGate Hub-spoke) ≠ "Thin Edge" (FortiAP/FortiExtender L2). Different routing, different management, different provisioning.

---

## 1. Strategic framing (Tier 3 — positioning, labeled as such)

Fortinet sells the **breadth of on-ramps** — agent (FortiClient), agentless (SWG/PAC + Secure Browser), thin-edge (FortiExtender/FortiBranchSASE/FortiAP), site/Branch On-Ramp (FortiGate IPsec), and FortiGate-native SPA — as a **single-vendor SASE differentiator**: one console, one FortiOS family, a continuum from "5 users on a 60G" to enterprise. Ordering-Guide framing: *"Companies with existing Fortinet deployments can seamlessly expand their network to include SASE locations that join natively with their SD-WAN, NGFW or DCFW segments… plus eliminates the need to architect & maintain complex routing configurations."* ([Ordering Guide p.1](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf)) — quote **CONFIRMED**; "differentiator" is positioning.

---

## 2. The five on-ramp families (overview)

| On-ramp | Endpoint requirement | Carries | Provisioning path |
|---|---|---|---|
| **Agent (FortiClient)** | FortiClient + EMS-in-cloud | Full-protocol SIA + ZTNA(TCP) + SSA | invitation code → Cloud Security tunnel |
| **Agentless (SWG)** | Browser + PAC, or Secure Browser ext | **Web only** (HTTP/HTTPS) | PAC file / GPO / Chrome ext |
| **Thin-edge** | FortiExtender / FortiAP / FortiBranchSASE | Whole-site (microbranch), L2 | **FortiZTP target = FortiSASE** |
| **Branch On-Ramp (BOR)** | FortiGate (or 3rd-party IKEv2) | Whole-site, agentless | **FortiZTP → FortiManager** → IPsec to BOR |
| **SPA / FortiGate-native** | FortiGate SPA hub | Private/DC apps | SD-WAN/SPA bundle + REST/Terraform |

---

## 3. Branch On-Ramp (BOR) — architecture, routing, scale

**Topology:** hub-and-spoke. BOR node = **Hub** (IPsec **dial-up server**); branch FortiGates = **Spokes**.
> "FortiGates will then connect to the BOR node in the **Hub-and-Spoke topology**, where BOR node is the Hub and branches are Spokes." / "BOR node acts as **IPsec dial-up server**… Each BOR node has a **unique public IP address and associated FQDN**." — [MSSP Arch Guide, BOR](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor) — **CONFIRMED**

**Dynamic tunnel IP via mode-config:**
> "BOR node has **mode-config** enabled under the IPsec tunnel and will assign unique IP to each of the connecting FortiGates from the subnet defined." — same — **CONFIRMED**

**iBGP only, same ASN, BGP-per-overlay:**
> "BOR nodes will assume that the on-ramp branches have the **same BGP ASN**… **only iBGP is supported** between BOR and on-ramp branches." / "Supported BGP design is **BGP per-Overlay**." — same — **CONFIRMED**
> Why per-overlay: "allows the On-Ramp to **see the source IP address of the client** connected behind the IPsec device." — [Mature 242700](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/242700/bgp-sd-wan-and-routing-configuration) — **CONFIRMED**

**Bidirectional traffic** (the payoff of mode-config + iBGP): "support traffic initiation in **both directions**, from and to on-ramp branches." — **CONFIRMED**

**Agentless behind the branch:** "The endpoints only need to be configured… to **forward traffic to the FortiGate as the default gateway**." / "FortiClient does **not** need to be installed… and web browser-based endpoints do **not** require explicit web proxy settings." — [Arch Guide 213023](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp) — **CONFIRMED**

**One shared dial-up tunnel serves all FortiGate branches:** "multiple IPsec tunnels can be defined under a single BOR node, but **only one tunnel is enough for accommodating all branches that connect with FortiGates**." — **CONFIRMED** (contrast third-party: dedicated tunnel per device — §4c).

### Scale & redundancy (exact numbers — CONFIRMED)
| Limit | Value |
|---|---|
| BOR nodes per tenant | **min 2, max 20** |
| Branch connections per node | **2000** |
| Bandwidth per node | **1 Gbps** (see nuance below) |
| Branches per tenant | **40,000** |
| Redundancy | a branch may connect to **multiple BOR nodes** |
| License | restricts # of On-Ramp locations **by seat count** |

⚠ **Pothole B1 — the bandwidth nuance (get this exactly right).** Both statements are true and must be stated together: the 1 Gbps is **shared across the up-to-2000 branch tunnels on that node**, AND it is **dedicated to the Branch On-Ramp Location — not pooled with Remote Users or Edge Devices**.
> "Each Branch On-Ramp Location includes **1 Gbps of shared bandwidth for up to 2000 supported connections**… **Bandwidth is dedicated to the Location and not shared with Remote Users or Edge Devices**." — [Ordering Guide p.10](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf) — **CONFIRMED**. (So: shared among branches on the node; dedicated vs other traffic pools. Don't say simply "dedicated" or simply "shared.")

⚠ **Pothole B2 — minimum 2 nodes.** A single-PoP BOR is not a supported topology; the floor of 2 *is* the baseline redundancy model. Size seats for 2..20.
⚠ **Pothole B3 — historical 10→2000.** Pre-25.3 a node supported only **10** dial-up connections; 25.3 raised it to **2000**. "Each on-ramp Security PoP provides up to 1 Gbps for up to 2000 simultaneous dialup IPsec connections, **changed from the previous limit of 10 connections**." ([25.3.139 release notes](https://docs.fortinet.com/document/fortisase/25.3.139/mature-release-notes/661728/whats-new)) — **PARTIALLY-CONFIRMED**. Old runbooks may quote 10.

**Shared SPA/BOR BGP config:** "Static routes are installed in the routing table, **redistributed into BGP, and advertised to the FortiGate Hubs through SPA connections and to the rest of the network, including SASE PoPs**." — **CONFIRMED**. **BGP MED** here is **observability** for SPA routes (`View Learned BGP Routes` / `Viewing MED values of SPA routes`), **not** a documented BOR↔branch tuning knob — **UNVERIFIED** as a knob.

---

## 4. Provisioning the site on-ramp (runbooks)

### 4a. Deploy the Branch On-ramp security PoP — SPA FIRST
⚠ **Pothole P1 (the #1 ordering gotcha):**
> "**You must configure the SPA network configuration first before deploying a Branch On-ramp location**, but SPA service connections can be created after… **BGP configuration is shared** between the Branch On-ramp and Secure Private Access (SPA) features." — [Arch Guide 213023](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp) — **CONFIRMED**

Workflow (Feature): `Operations > Connectivity > On-ramp tunnel` → **Security PoP** tab → **Deploy security PoP** → status **Pending → Running** → click **+** to add PoPs "as your FortiSASE Branch On-ramp subscription allows." ([Feature 166485](https://docs.fortinet.com/document/fortisase/26.1.26/feature-administration-guide/166485)) — **CONFIRMED**. Mature equivalent: `Edge Devices > SD-WAN On-Ramp > On-Ramp locations > Deploy On-Ramp location`. The page emits the **FQDN + tunnel-interface IP** used in branch config. ⚠ Post-deploy: allow a few minutes after **Running** before the FQDN answers pings.

### 4b. FortiGate branch — the FortiManager path (HEADLINE PROVISIONING FACT)
⚠ **Pothole P2 — FortiGate is NOT a FortiZTP target for FortiSASE.** In FortiZTP, a FortiGate's only targets are FortiGate Cloud / FortiManager / FortiManager Cloud. FortiSASE does **not** appear as a FortiGate target.
> *Provisioning a FortiGate* (FortiZTP 26.1.a) lists only "To provision a FortiGate to FortiGate Cloud / FortiManager / FortiManager Cloud." — [FortiZTP 26.1.a](https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/574054/provisioning-a-fortigate) — **CONFIRMED**.

So the branch FortiGate reaches FortiSASE **indirectly**: provision **FortiZTP → FortiManager(Cloud)**, FortiManager installs the SD-WAN/on-ramp template, the FortiGate dials **IPsec into the FortiSASE BOR**. (Only FortiGate is the supported certified IPsec device for Mature BOR: "the **FortiGate is the only supported IPsec device**." — **CONFIRMED**.)

**FortiManager golden config** (SD-WAN Overlay Template + model device): WAN interfaces, dual IPsec overlays to the BOR, **one BGP session per overlay** (or **BGP-on-loopback**, FMG 7.6), **bootstrap static routes to hub loopbacks**, per-branch **performance-SLA health checks** to the hub `Lo-HC`, security profiles.
> "The SD-WAN Overlay Template can deploy **BGP on loopback interfaces**… greatly reduces the number of routes advertised." — [FMG 7.6.0 new features](https://docs.fortinet.com/document/fortimanager/7.6.0/new-features/899964/sd-wan-overlay-template-can-deploy-bgp-on-loopback-interfaces) — **CONFIRMED**
> Branch BGP example: Local AS **65001**, Remote AS **65001** (iBGP/same-ASN), Router ID = the mode-config-assigned tunnel IP. — [Mature 242700](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/242700/bgp-sd-wan-and-routing-configuration) — **CONFIRMED**

**Day-0 behavior — CONFIRMED** ([FMG Cloud 7.6.6](https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud)):
- With model device: "FGFM tunnel is established. The **auto-link** process is performed automatically."
- Without preconfig: lands in **Unauthorized Devices** → manual authorize.
- Physical units: "you must perform a **factory reset**."
- "Deprovisioning a device from the FortiZTP portal **will not delete** the device from FortiManager Cloud."
⚠ **Pothole P3:** FMG Cloud **no longer auto-creates** the model device on provision — pre-create it yourself ([FortiZTP 25.4.0](https://docs.fortinet.com/document/fortiztp/25.4.0/administration-guide/574054/provisioning-a-fortigate)). ⚠ **P4:** true ZTP only for FortiGate **≤100F**; larger models are **one-touch**. ⚠ **P5:** the FortiGate needs a **Fortinet-signed cert (SN as CN)** for FortiZTP.

### 4c. Third-party / custom IPsec device (the constrained path)
⚠ **Pothole P6 — third-party gaps (steer customers to FortiGate):**
- **IKEv2 mandatory:** "Connecting devices need to support and use **IKEv2** to connect to BOR node." — **CONFIRMED**
- **Disable mode-config:** "if the Branch device does **not support this feature, ensure the Network > Mode config setting is set to Disabled**." — **CONFIRMED**
- **No BGP → static + SNAT:** "**BGP is not supported when using third-party branch devices, static routing must be configured**" + source-NAT on the branch policy for reply traffic. — **CONFIRMED**
- **Dedicated tunnel + unique IDs per device:** "configure each tunnel with a **unique peer ID** and set the **local ID on each branch device to match**." — **CONFIRMED**
- **Outbound-only without mode-config:** "without mode-config… Hub-Spoke topology will support **only outbound traffic (branch to SASE)**, whilst **inbound traffic (SASE to branch) will not be possible**." — [MSSP Arch Guide, BOR](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor) — **CONFIRMED**

### 4d. Thin-edge (FortiExtender / FortiAP / FortiBranchSASE) — FortiZTP target = FortiSASE
Unlike the FortiGate, thin edges **do** provision straight to FortiSASE. Verbatim FortiZTP runbook ([Connecting a FortiAP to FortiSASE using FortiZTP](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/299731/connecting-a-fortiap-to-fortisase-using-fortiztp) — **CONFIRMED**):
1. FortiCloud → **Products > Register More** → enter device serial; repeat for the **FortiSASE Subscription / ThinEdge License** code.
2. Confirm **Entitlement lists "FortiSASE Subscription"** (⚠ **Pothole P7:** must show *before* provisioning).
3. FortiSASE → **Services > FortiZTP > Setting** → on the device tab ensure **FortiSASE** enabled → **UPDATE**.
4. **UNPROVISIONED** tab → select device(s) → **PROVISION** → **TARGET LOCATION = FortiSASE** → **PROVISION NOW**.

**Thin-edge specifics:**
- **FortiExtender LAN Extension** = microbranch; with IPAM "**Creates a DHCP server entry**… to automatically provide addresses to clients on the LAN extension interface." — **CONFIRMED / PARTIALLY-CONFIRMED**
- **Counts:** max **1024 FortiExtender** and **240 FortiAP** per account (**PARTIALLY-CONFIRMED**, snippet). FortiExtender→FortiSASE ZTP needs **FortiOS 7.2.3+** (200F 7.4.3+); FortiAP edge needs **FAP firmware 7.2.4+** — **CONFIRMED**.
- **FortiBranchSASE** (10F-WiFi / 20G / 20G-WiFi) is part of the FortiExtender family; "Topics referencing FortiExtender… also apply to FortiBranchSASE." — **CONFIRMED**
- ⚠ **Pothole P8:** thin-edge **still consumes a FortiSASE user seat license** (and a per-FortiExtender subscription). "Thin Edge are managed directly in FortiSASE portal. **User license is still required.**" — [Ordering Guide p.4](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf) — **CONFIRMED**.

---

## 5. User on-ramps — provisioning + potholes

### 5a. Agent (FortiClient "Cloud Security" tunnel)
- The tunnel **is** the on-ramp; historically **full-tunnel SSL VPN**; onboard via **invitation code**. — [SIA agent-based 25.3.139](https://docs.fortinet.com/document/fortisase/25.3.139/architecture-guide/710519/sia-for-agent-based-remote-users) — **CONFIRMED**
- **Split tunnel = Windows only** (app-based); other OS = full tunnel. — **CONFIRMED**
- **ZTNA on-ramp** for private apps = **TCP-only**, agent + client cert from EMS. — [SPA via ZTNA](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/472920/secure-private-access-using-ztna) — **CONFIRMED**

⚠ **Agent potholes (all CONFIRMED unless noted):**
- **A1 — SSL→IPsec forced migration "early 2027"** for the Cloud Security tunnel; transition/hybrid mode is opt-in now. **PARTIALLY-CONFIRMED** — plan ahead.
- **A2 — IPsec and SSL VPN are mutually exclusive per instance:** "All remote VPN users for an instance must use only one connectivity method." Recommended IPsec client = FortiClient 7.2.14. **IPsec-over-TCP/443** (25.4) for networks blocking UDP 500/4500.
- **A3 — QUIC (UDP 443) must be blocked** for SSL deep inspection (or use the newer HTTP/3-inspection action). Test via `https://quic.nginx.org/`.
- **A4 — FortiClient drops IPv6:** "Only IPv4 traffic traverses through the FortiSASE tunnel."
- **A5 — >100 users behind one source IP** → must move off the agent on-ramp to **Branch On-Ramp / Thin Edge / FortiGate Secure Edge**.
- **A6 — agent egress needs UDP 500/4500.**
- **A7 — IPsec on-ramp can't use LDAP** (use RADIUS / FortiAuthenticator).
- **A8 — SSL-VPN policy changes need a user reconnect** to take effect; an SSL-VPN allow policy must exist for any tunnel.
- **A9 — FIDO2 needs an external browser** (FortiClient mini-browser unsupported). A **Windows-specific** FIDO2 caveat is **UNVERIFIED** (only the generic + macOS/Safari conditions are documented).

### 5b. Agentless (SWG)
- Explicit proxy via **hosted PAC**; **web only** — "All other non-web traffic bypasses FortiSASE." No ZTNA. SAML/LDAP/RADIUS auth on the listener; client must trust the FortiSASE proxy CA. — [SIA agentless 25.1.39](https://docs.fortinet.com/document/fortisase/25.1.39/architecture-guide/834810/sia-for-agentless-remote-users) — **CONFIRMED**
- Automate proxy config via **GPO / SCCM**; **SWG Chrome extension** for Chromebooks/managed Chrome. — **CONFIRMED / PARTIALLY-CONFIRMED**
- **Secure Browser extension (26.1)** for unmanaged/contractor devices — full browser visibility **without DPI**. ⚠ **Pothole A10:** Secure Browser/RBI are **"select availability" — require a FortiCare ticket** (same gate as central management; see `04-fortimanager-managed-fortisase.md` §1). **PARTIALLY-CONFIRMED**.
- ⚠ **Pothole A11: SWG mode unsupported on iOS.** — **CONFIRMED**

---

## 6. PoP selection (part of every on-ramp)
- **Closest PoP by egress public-IP geolocation:** "FortiSASE directs your endpoint to the **closest security PoP based on the specific geolocation information of your endpoint's public IP address**." — **PARTIALLY-CONFIRMED**
- **Pick PoPs near users at init**; ⚠ **Pothole PoP1 — use an ECS-capable resolver** or you get **PoP flapping**: "intermittently ending up in different security PoPs from the same physical location… your system's defined resolving name servers are geolocating to different locations." Verify ECS via a second TXT record in dig/nslookup. — [Security PoPs 25.3.89](https://docs.fortinet.com/document/fortisase/25.3.89/feature-administration-guide/295668/security-pops) — **PARTIALLY-CONFIRMED**
- **Dedicated egress IPs:** "Each… Security PoP can support up to **5 dedicated egress IPs (DEIPs), 4** of these… for source IP anchoring rules." **Geolocation rules** map an out-of-region public IP to a PoP for compliance. — [Geolocation rules 26.1.92](https://docs.fortinet.com/document/fortisase/26.1.92/feature-public-ip-deployment-guide/841750/geolocation-rules) — **CONFIRMED**

---

## 7. On-ramp licensing (Ordering Guide rev FSS-OG-R40, 2026-05-25 — CONFIRMED unless noted)
- **Branch On-Ramp Location (1 Gbps node):** `FC1-10-EMS05-769-02-DD` (Fortinet Cloud PoP) / `FC1-10-EMS05-770-02-DD` (Public Cloud PoP). Standard = Fortinet-Cloud PoPs only; Advanced/Comprehensive = both. (Retailers also list these as "FortiSASE SD-WAN On-Ramp Location.")
- **Node capacity:** 1 Gbps / 2000 conns; **max 20 locations & 40,000 connections per account**; **≥2 for redundancy**.
- **Seat-based location caps:** "Standard and Advanced… include up to **4 locations**… Comprehensive **<200 users** include **1–2 locations**." Up to **16 add-on** locations → 20 max. ⚠ **Pothole L1:** small Comprehensive tenants are PoP-constrained.
- **Branch On-Ramp connection add-on (1–2000 FortiGate IPsec connections)** introduced **25.1** — **PARTIALLY-CONFIRMED**.
- **Branch on-ramp with Standard subscription** added **25.3**; 2026 OG shows it Standard-included. ⚠ **Pothole L2 (version drift):** an older 25.3 abstract said a Standard instance *also* needs an Advanced branch-on-ramp add-on — **UNVERIFIED / version-dependent**; validate against the tenant's release.
- **Thin-edge/branch still needs a user seat license** (OG p.4/p.10).
- **FortiGate-native entry = SD-WAN/SPA bundle:** "supported on F-series and G-series FortiGate models **starting with the 60G**… as little as **5 users**." Seats by model: 60G+ → 5, 100F+ → 10, 700G+ → 50, 1800F+ → 100 (SKU `…-1329`/`…-1389`; only 1329 includes FortiCare Premium). SPA license is **per hub** (and per HA member). (Corrects the older "120G/10-user" note.)
- **Seat mechanics:** consumed at first device registration; released after **45 days** no telemetry; **3 devices/user** (4th consumes a seat).

---

## 8. Monitoring & troubleshooting (per on-ramp)

**Agent on-ramp up?** FortiClient **Remote Access = Connected**; admin side `Dashboards > Status` → **User Connection Monitor** + **Managed Endpoints** show online; per-endpoint PoP/session under `Operations > Connectivity > Endpoints`. — **CONFIRMED / PARTIALLY-CONFIRMED**

**IPsec branch on-ramp up? (ordered checks — CONFIRMED, [Mature 270224](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/270224/verifying-and-troubleshooting-ipsec-vpn-connection)):**
1. PoP `Status = Running` (else wait / re-deploy).
2. FortiGate-side: `diag sys waninfo ipify` (WAN IP) → `exec ping <PoP FQDN>` (allow minutes post-deploy).
3. `Dashboard > Network > IPsec` widget — tunnel established.
4. IKE debug: `diag debug application ike -1` → `diag debug enable`; verify Phase 1 = **DDNS FQDN, IKEv2, correct PSK, `set network-overlay enable` / `set network-id 1`**.
5. **Health and VPN Tunnel Status** page — IPsec + **BGP peering state** + health-check IP; `View Learned BGP Routes`.

**Agentless?** Confirm browser auto-proxy URL resolves the hosted PAC, HTTP/HTTPS egress lands on the SWG public IP, FortiSASE proxy CA trusted. ⚠ Exact PAC-test pages 404'd → procedure **UNVERIFIED**; verify live.

**Common failure modes:** PoP still **Pending** / FQDN not resolving; **SPA config not done first** → tunnel up but routes don't propagate; **third-party mode-config left enabled** → IP mismatch; **non-unique Local/Peer ID** → wrong tunnel matched; **branch ASN ≠ FortiSASE ASN** → iBGP won't form; **non-ECS resolver** → PoP flapping; **UDP 500/4500 blocked** → use IPsec-over-TCP/443.

---

## 9. Master pothole catalog (one place)

| # | Pothole | Status |
|---|---|---|
| N1 | "SD-WAN On-Ramp" (Mature) vs "On-ramp tunnel" (Feature) = same feature, different menu | CONFIRMED |
| N2 | Branch On-ramp (FortiGate IPsec) ≠ Thin Edge (FortiAP/FortiExtender L2) | CONFIRMED |
| P1 | **SPA network config must exist before deploying a BOR** (shared BGP) | CONFIRMED |
| P2 | **FortiGate is NOT a FortiZTP target for FortiSASE** — go via FortiManager | CONFIRMED |
| P3 | FMG Cloud no longer auto-creates the model device | CONFIRMED |
| P4 | True ZTP only FortiGate ≤100F; larger = one-touch | CONFIRMED |
| P5 | FortiGate needs Fortinet-signed cert (SN as CN) for ZTP | CONFIRMED |
| P6 | Third-party device: IKEv2, disable mode-config, static+SNAT, dedicated tunnel/unique IDs, **outbound-only** | CONFIRMED |
| P7 | Thin-edge entitlement must show "FortiSASE Subscription" before provisioning | CONFIRMED |
| P8 | Thin-edge still consumes a user seat license | CONFIRMED |
| B1 | 1 Gbps is **shared across branches** yet **dedicated vs other traffic pools** — state both | CONFIRMED |
| B2 | Minimum 2 BOR nodes (single-PoP not supported) | CONFIRMED |
| B3 | Pre-25.3 node = 10 conns; now 2000 (old runbooks) | PARTIALLY-CONFIRMED |
| A1 | Cloud Security tunnel **SSL→IPsec forced migration early 2027** | PARTIALLY-CONFIRMED |
| A2 | IPsec & SSL VPN mutually exclusive per instance | CONFIRMED |
| A3 | Block QUIC (UDP 443) for SSL DPI | CONFIRMED |
| A4 | FortiClient drops IPv6 | CONFIRMED |
| A5 | >100 users/shared source IP → move off agent to Branch/ThinEdge/Secure Edge | CONFIRMED |
| A7 | IPsec on-ramp can't use LDAP | CONFIRMED |
| A8 | SSL-VPN policy changes need user reconnect | CONFIRMED |
| A9 | FIDO2 needs external browser; **Windows-specific caveat UNVERIFIED** | PARTIALLY-CONFIRMED |
| A10 | Secure Browser/RBI are select-availability → **FortiCare ticket** | PARTIALLY-CONFIRMED |
| A11 | SWG mode unsupported on iOS | CONFIRMED |
| L1 | Comprehensive <200 users → PoP-limited (1–2 locations) | CONFIRMED |
| L2 | Standard-needs-Advanced-add-on for branch on-ramp — version drift | UNVERIFIED |
| PoP1 | Non-ECS resolver → PoP flapping | PARTIALLY-CONFIRMED |
| MED | BGP MED as a BOR↔branch tuning knob (it's observability only) | UNVERIFIED |

---

## 9.5 Worked design — ONE FortiGate as both SPA hub + BOR branch (incl. the 30G question)

> **Question that drove this:** "FortiOS is FortiOS — can a single small FortiGate (e.g. 30G) be a **SPA hub** (private access for off-net users) **and** a **BOR branch** (its own internet/SIA egress) at the same time?" Cross-verified June 2026. **Net: BGP-coherent and buildable on one ASN; NOT a Fortinet-validated single-box topology — lab + TAC before a customer SOW.**

### Role boundaries (the mental model)
- **BOR = egress/on-ramp.** The FortiGate is the IPsec **dial-up client**; the BOR PoP is the server. Documented uses: branch→internet (SIA) and branch's own outbound SPA. (corpus refs §3–§4)
- **SPA hub = ingress for private access.** The FortiSASE PoPs are the **dial-up clients**; the FortiGate is the **server** (ADVPN receiver-mode). This is how off-net/remote users reach private apps. The hub is documented as a **"standalone"** NGFW.
  - **Public-IP rule (gets mis-sold):** only the **SPA-hub site** needs a **directly-assigned public IP on its WAN** — *"the FortiGate Hub needs to be accessible from the Internet… directly assigned public IP addresses on its ISP interfaces."* The IP may be **dynamic** — **FQDN/DDNS names it** (FortiOS FQDN-remote-gateway). FQDN is *not* a substitute for having a public IP; it just lets the IP be dynamic.
  - **Spoke / BOR-branch sites need NO public IP** — they're dial-up *clients* (behind NAT / dynamic / LTE is fine); they target the BOR location/hub **FQDN**, and mode-config assigns their tunnel IP.
  - **Do not conflate** the hub's ISP public IP (free, from the customer's ISP, not a SKU) with **FortiSASE Dedicated *egress* IPs** (`FC1-10-EMS05-658`, cloud-side PoP egress for source-IP anchoring/allowlisting) — different layer.
  - **In the 30G dual-role build:** one WAN public IP (static or dynamic+DDNS) covers it — inbound IKE for SPA + outbound IKE for BOR coexist on the same WAN; everything behind it needs nothing public.
- **Anything *into* a site — remote users, other branches, private apps — goes through a SPA hub, not BOR.** (See §3.4 and the remote-to-site / branch-to-branch findings.)

### The 30G capability/sizing reality
- **30G as a BOR branch / SD-WAN spoke: supported** (no documented model floor; 30G is the floor of the per-device SPA SKU `-1337`).
- **30G as a SPA hub: technically allowed but role-mismatched.** Fortinet: *"FortiGate 100F series and later are recommended for an SD-WAN hub. FortiGate desktop platforms are recommended as a single NGFW location only."* 30G = ~500 Mbps Threat Protection, 200 gateway-to-gateway tunnels, no SSL-VPN. **Fine for one tiny single-site hub; do not scale.** Use **100F+/700G+** for a real multi-PoP hub.

### The BGP design that makes one box work — ONE ASN, iBGP (CONFIRMED)
This is the crux, and it resolves in favor of the design:
- **BOR mandates** the branch use FortiSASE's ASN, **iBGP only**: *"BOR nodes will assume that the on-ramp branches have the same BGP ASN as defined on FortiSASE… only iBGP is supported between BOR and on-ramp branches."* ([BOR, MSSP Arch Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor))
- **SPA hub recommends the same:** *"Recommendation is to use the same ASN on both sides (iBGP), FortiSASE and the remote FortiGate Hub."* ([SPA, MSSP Arch Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/588241/secure-private-access-spa)) — verified on a live hub: `local AS number 65400`, all PoP neighbors AS 65400 = iBGP.
- **BGP config is shared between BOR and SPA** (*"BGP configuration is shared between the Branch On-ramp and Secure Private Access (SPA) features."*) → **one FortiSASE tenant ASN** for the SPA hub AND the BOR branch.
- ⟹ On the box: `config router bgp → set as <FortiSASE-tenant-ASN>` **once**. That single local-AS serves both the inbound SPA-hub iBGP and the outbound BOR iBGP. **The only break: choosing the OPTIONAL eBGP/different-ASN SPA model — it conflicts with BOR's iBGP-only rule. Don't.**

### The functional split (clean)
- **SPA tunnels → private subnets** (specific routes; PoPs dial in; remote users reach private apps).
- **BOR tunnel → internet/SIA** (default route + source-NAT; site's plain egress inspected at the BOR PoP).
- Separate phase-1s on the same WAN — no FortiOS conflict (one interface is both dial-up server for SPA and dial-up client for BOR).

### The 4 things to lab-validate (the real risks)
1. **Self-origination route loop (#1).** FortiSASE redistributes BOR-learned routes into SPA; the same box is BOR-originator *and* SPA-hub route-reflector → its own LAN prefix can return to it via SPA. Inside one ASN, AS-path loop-prevention doesn't apply — you rely on **RR Originator-ID/Cluster-list**. **Watch the box's BGP table for its own prefix arriving via SPA; add a route-map/community filter on locally-originated BOR prefixes if seen.**
2. **Default-vs-specific asymmetry.** Default→BOR (internet), specific→SPA (private). Ensure remote-user/PoP source subnets are learned as **specific** SPA routes or return traffic leaks out the BOR default.
3. **Mixed BGP methods.** BOR↔branch adjacency is **always per-overlay**; SPA hub ideally runs **BGP-on-loopback** (MSSP reference). One box runs both (separate neighbor-groups) — confirm.
4. **Sizing.** Desktop 30G is now SPA hub + route-reflector + BOR client + inspection at once. Single tiny site only.

### Licensing (stacks; not mutually exclusive)
- SPA on the box: `FC-10-XXXXX-1337` (FGT-30G+, part of SD-WAN Service Bundle; SPA license required on hub locations, each HA member its own).
- BOR: cloud-side **Branch On-Ramp Location** `FC1-10-EMS05-769`/`-770` (**min 2** for redundancy) + **user seats**.

### TAC/PM question to get it blessed (2 lines)
1. *Is a single FortiGate supported acting simultaneously as a FortiSASE **SPA hub** (PoPs dial in) and a **Branch On-Ramp branch** (dials out to a BOR PoP), on one tenant ASN / iBGP?*
2. *If so, what loop-prevention (route-map / community / split-horizon) do you require so the box's own BOR-originated prefixes are not reflected back via the SPA path?*

**Status:** every building block CONFIRMED and mutually consistent; the **collapsed single-box dual role is UNVERIFIED/NOT-DOCUMENTED** — treat as lab-validated-then-TAC-confirmed, not as a sanctioned reference design.

---

## 10. Sources (consolidated)

- [Branch On-Ramp (BOR) — Unified SASE for MSSP Arch Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor)
- [Thin Edge — Unified SASE for MSSP Arch Guide](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/829351/thin-edge)
- [SD-WAN On-Ramp — Mature Admin Guide](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp)
- [Configuring IPsec device as Branch On-ramp — Mature](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/597998/configuring-ipsec-device-as-branch-on-ramp)
- [BGP, SD-WAN, and routing configuration — Mature](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/242700/bgp-sd-wan-and-routing-configuration)
- [Site-based remote users using Branch On-ramp — Arch Guide](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp)
- [Deploying a Branch On-ramp security PoP — Feature 26.1.26](https://docs.fortinet.com/document/fortisase/26.1.26/feature-administration-guide/166485)
- [Configuring an IPsec tunnel for the custom device type — Feature](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/326899/configuring-an-ipsec-tunnel-for-the-custom-device-type)
- [Verifying and troubleshooting IPsec VPN connection — Mature](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/270224/verifying-and-troubleshooting-ipsec-vpn-connection)
- [Viewing health and VPN tunnel status — Feature](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/322097/viewing-health-and-vpn-tunnel-status)
- [Connecting a FortiAP to FortiSASE using FortiZTP — Mature](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/299731/connecting-a-fortiap-to-fortisase-using-fortiztp)
- [FortiExtender — Mature Admin Guide](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/849777/fortiextender)
- [FortiAP — Mature Admin Guide](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/182725/fortiap)
- [Common use cases (supported models/firmware) — Mature Release Notes 26.1.107](https://docs.fortinet.com/document/fortisase/26.1.107/mature-release-notes/969608/common-use-cases)
- [Provisioning a FortiGate — FortiZTP 26.1.a](https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/574054/provisioning-a-fortigate)
- [Provisioning a FortiExtender — FortiZTP 26.1.a](https://docs.fortinet.com/document/fortiztp/26.1.a/administration-guide/681571/provisioning-a-fortiextender)
- [Provisioning a FortiAP — FortiZTP](https://docs.fortinet.com/document/fortiztp/latest/administration-guide/373908/provisioning-a-fortiap)
- [Using FortiZTP with FortiManager Cloud — 7.6.6](https://docs.fortinet.com/document/fortimanager-cloud/7.6.6/cloud-deployment/552626/using-fortiztp-with-fortimanager-cloud)
- [SD-WAN Overlay Template can deploy BGP on loopback — FMG 7.6.0](https://docs.fortinet.com/document/fortimanager/7.6.0/new-features/899964/sd-wan-overlay-template-can-deploy-bgp-on-loopback-interfaces)
- [SIA for agent-based remote users — 25.3.139](https://docs.fortinet.com/document/fortisase/25.3.139/architecture-guide/710519/sia-for-agent-based-remote-users)
- [Traffic steering method with FortiClient — 26.1.107](https://docs.fortinet.com/document/fortisase/26.1.107/secure-internet-access-architecture-guide/33886/traffic-steering-method-with-forticlient)
- [IPsec VPN remote user support — Mature](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/897609/ipsec-vpn-remote-user-support)
- [Secure private access using ZTNA — Arch Guide](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/472920/secure-private-access-using-ztna)
- [SIA for agentless remote users — 25.1.39](https://docs.fortinet.com/document/fortisase/25.1.39/architecture-guide/834810/sia-for-agentless-remote-users)
- [Secure Browser — Feature Admin Guide](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/407814/secure-browser)
- [Security PoPs — 25.3.89](https://docs.fortinet.com/document/fortisase/25.3.89/feature-administration-guide/295668/security-pops)
- [Geolocation rules — 26.1.92](https://docs.fortinet.com/document/fortisase/26.1.92/feature-public-ip-deployment-guide/841750/geolocation-rules)
- [Blocking QUIC — 26.1.107](https://docs.fortinet.com/document/fortisase/26.1.107/mature-administration-guide/219936/blocking-quic)
- [Limitations — Mature Release Notes](https://docs.fortinet.com/document/fortisase/latest/mature-release-notes/49049/limitations)
- [FortiSASE Ordering Guide PDF (FSS-OG-R40, 2026-05-25)](https://www.fortinet.com/content/dam/fortinet/assets/data-sheets/og-fortisase.pdf)

---

## 11. Verdict ledger (key claims)

| Claim | Status | Version |
|---|---|---|
| SD-WAN On-Ramp == Branch On-ramp (one feature, two menu names) | CONFIRMED | Mature 25.x / Feature 26.1.x |
| Thin-edge (FortiAP/FortiExtender L2) is a distinct model from BOR | CONFIRMED | latest |
| BOR = hub-and-spoke, IPsec dial-up, mode-config tunnel IPs, iBGP/same-ASN/per-overlay, bidirectional | CONFIRMED | latest / MSSP guide |
| Endpoints behind branch are agentless (FortiGate = default gateway) | CONFIRMED | latest |
| **SPA network config must precede BOR deployment** | CONFIRMED | latest |
| min 2 / max 20 BOR nodes; 2000 conns & 1 Gbps/node; 40,000/tenant | CONFIRMED | MSSP guide / OG |
| 1 Gbps shared-across-branches yet dedicated-vs-other-pools | CONFIRMED | OG p.10 |
| Pre-25.3 node = 10 conns → 2000 | PARTIALLY-CONFIRMED | 25.3.x |
| FortiGate is the only supported certified IPsec device (Mature BOR) | CONFIRMED | Mature 26.1 |
| **FortiGate is NOT a FortiZTP target for FortiSASE** (FGT→FMG only) | CONFIRMED | FortiZTP 26.1.a/25.4.0 |
| Thin-edge (FortiAP/FortiExtender/FBS) **is** a FortiZTP target=FortiSASE | CONFIRMED | FortiZTP 26.1.a |
| Third-party: IKEv2, no mode-config, static+SNAT, dedicated tunnel/unique IDs, outbound-only | CONFIRMED | Feature / MSSP guide |
| FMG day-0 (FGFM/auto-link; Unauthorized w/o preconfig; factory reset; deprovision≠delete) | CONFIRMED | FMG Cloud 7.6.6 |
| Max 1024 FortiExtender / 240 FortiAP per account | PARTIALLY-CONFIRMED | 26.1.x |
| Thin-edge still consumes a user seat | CONFIRMED | OG p.4/p.10 |
| Agent tunnel SSL default; split=Windows only; ZTNA=TCP-only | CONFIRMED | 25.3.139 / latest |
| SSL→IPsec forced migration early 2027; IPsec/SSL mutually exclusive | PARTIALLY/CONFIRMED | 25.4 / latest |
| QUIC must be blocked; IPv6 dropped; >100/shared-IP → off agent; UDP 500/4500 | CONFIRMED | 26.1.107 |
| IPsec on-ramp can't use LDAP; SSL policy change needs reconnect; SWG not on iOS | CONFIRMED | latest |
| Agentless SWG = web only, PAC, SAML; Secure Browser = select-availability (ticket) | CONFIRMED / PARTIALLY | 25.1 / 26.1 |
| Closest PoP by egress-IP geo; ECS resolver to avoid flapping; 5 DEIPs/PoP | PARTIALLY/CONFIRMED | 25.3.89 / 26.1.92 |
| BOR Location SKUs -769/-770; seat-based location caps; Comp<200 PoP-limited | CONFIRMED | OG 2026 |
| SD-WAN/SPA bundle = FortiGate on-ramp entry, 60G+/5 users | CONFIRMED | OG p.3 |
| Standard-needs-Advanced-add-on for branch on-ramp | UNVERIFIED (version drift) | — |
| BGP MED as a BOR↔branch knob | UNVERIFIED | — |
| Windows-specific FIDO2 caveat | UNVERIFIED | — |
