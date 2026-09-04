# FortiSASE: Architecture & On-Ramp Types — SE Corpus Reference

> **Tier 1 (official Fortinet docs).** Compiled June 2026 from docs.fortinet.com. Reflects FortiSASE **25.3.x / 26.1.x** doc streams. Every non-trivial claim carries an inline `(Source: <url>)`. Items that could not be confirmed against an exact page are flagged **UNVERIFIED — needs SE confirmation**.
> **Focus:** architecture + on-ramp connectivity models, oriented to a service offering centered on on-ramps and automation.
> **➜ For the engineering deep-dive** (provisioning runbooks, the full pothole catalog, taxonomy map, scale numbers, and the headline fact that *FortiGate is not a FortiZTP target for FortiSASE*), see [`05-on-ramp-deep-dive.md`](05-on-ramp-deep-dive.md). Where this doc and 05 differ on bandwidth wording or ZTP targets, **05 supersedes**.

---

## 1. Solution Overview

FortiSASE is Fortinet's cloud-delivered SASE platform combining **Security Service Edge (SSE)** with **SD-WAN**. SASE is defined by Fortinet as an architecture that "combines network, security, and WAN capabilities delivered as a service to provide endpoints (remote users, devices, and branches) with secure internet, cloud, and data center network access." The cloud-delivered security service sits "between the remote endpoints and any networks those endpoints access, regardless of the location of the remote endpoints" (Source: https://docs.fortinet.com/document/fortisase/25.3.112/concept-guide/832511/sase-architecture).

**Unified underpinnings.** FortiSASE is not a separate codebase — it is assembled from the existing Fortinet stack:

- **FWaaS** "based on FortiOS next generation firewall (NGFW) features."
- **SWG** "based on FortiOS explicit web proxy, captive portal, and authentication features."
- **Endpoint Management Service based on FortiClient EMS** (delivered as EMS-in-the-cloud / FortiClient Cloud).
- **FortiClient** for agent-based endpoint connectivity; "FortiClient Agent-Based software is a requirement for ZTNA since it provides device information, user information, and security posture."
- **FortiGuard Labs** threat intelligence consumed by FWaaS and SWG.
- **Global security points of presence (PoPs)** (Source: https://docs.fortinet.com/document/fortisase/26.1.107/architecture-guide/87005/technology-used).

**Security PoPs run in two infrastructures:** Fortinet Cloud locations and Public Cloud locations. At provisioning, "a customer's FortiSASE administrator configures four FortiSASE security points of presence (PoPs) and one FortiSASE log storage PoP by selecting from a list of distinct global data centers." Comprehensive-tier instances "can select a combination of Fortinet and Public Cloud locations" with "an unlimited number of Public Cloud locations" selectable (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/751044/appendix-a-fortisase-data-centers).

**Management console.** FortiSASE is administered through its own cloud portal (the FortiSASE management console, accessed via FortiCloud). It can additionally be co-managed by FortiManager (see §6).

---

## 2. The Four Core Capability Pillars & On-Ramp Mapping

FortiSASE organizes its SSE functions into capability pillars. Each pillar is delivered to traffic that reaches a security PoP via one or more **on-ramps** (the on-ramp determines *how* traffic gets to the PoP; the pillar determines *what inspection* happens there).

### Secure Internet Access (SIA)
Off-net endpoint traffic is redirected to the closest PoP and passed "through a firewall-as-a-service or a secure web gateway" before reaching the internet (Source: https://docs.fortinet.com/document/fortisase/25.3.112/concept-guide/832511/sase-architecture). **On-ramps:** agent-based (FortiClient tunnel), agentless (SWG explicit proxy / PAC), and site-based (Branch On-ramp). SIA has dedicated architecture and deployment guides per on-ramp (the SIA Site-Based and SIA Agentless SWG deployment guides).

### Secure Private Access (SPA)
Provides remote users secure access to private/internal applications. FortiSASE supports two models:
- **SPA using SD-WAN** — FortiSASE security PoPs join the customer's hub-and-spoke as spokes to FortiGate hub(s) over IPsec VPN overlays + BGP.
- **SPA using a FortiGate converted to a standalone FortiSASE SPA hub** — supports **up to 12 FortiGate hubs**.

The topology is hub-and-spoke where "the security points of presence (PoPs) act as spokes to the FortiGate hub," and **ADVPN** lets spokes establish dynamic on-demand direct tunnels. **ZTNA** (agent-based, FortiClient-required, TCP applications only) is the other SPA access method (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/443423/spa). See §3 (SPA hubs) for hub-selection detail.

### Secure SaaS Access (SSA) / CASB / Inline-DLP
FortiSASE delivers SaaS controls **inline** and via **API**:
- **Inline-CASB:** "FortiSASE uses Application Control to act as an Inline-CASB by providing access control to SaaS cloud application traffic," and "uses Web Filter with an Inline-CASB security component to customize headers" via HTTP header insertion to restrict SaaS *tenants* (e.g., block personal Microsoft 365 tenants). Works for both agentless (SWG) and agent-based (FortiClient) users.
- **Inline-DLP:** scans traffic against sensitive-data patterns and allows/blocks/logs on match.
- **API-CASB via FortiCASB:** out-of-band, "obtaining data directly from SaaS cloud applications such as Office 365 or Dropbox using REST API queries with OAuth2.0 authentication."
- **Requirements/licensing:** Inline-CASB web filter, app control, and DLP "do not require any special licenses beyond per-user FortiSASE licensing." **SSL deep inspection must be enabled and QUIC must be blocked** to inspect TLS traffic (Source: https://docs.fortinet.com/document/fortisase/latest/architecture-guide/770469/ssa-using-fortisase-inline-casb).

### Thin-Edge / Branch fit
Thin-edge devices (FortiExtender, FortiAP, FortiGate) "intelligently offload traffic to a SASE location for comprehensive security inspection at scale, for all devices" — i.e., they are the *site-based on-ramp* mechanism that brings whole-site traffic into the SIA/SPA/SSA pillars without per-endpoint agents (Source: https://www.fortinet.com/products/sase). FortiExtender can also operate as a **FortiSASE LAN Extension** (DHCP-assigning IPs to devices on its LAN switch interface) (Source: https://docs.fortinet.com/document/fortisase/24.3.56/administration-guide/982382/thin-edge).

---

## 3. On-Ramp Types In Depth (Priority Focus)

An **on-ramp** is the connectivity method that steers user or site traffic into a FortiSASE security PoP. The four operational families are below.

### 3.1 Agent-Based On-Ramp (FortiClient — VPN tunnel / SWG / ZTNA)
**Who:** remote/roaming users on managed endpoints.
**Agent/device:** FortiClient (agent-based mode), managed by EMS-in-the-cloud (FortiClient Cloud).
**How it connects:** the endpoint "connect[s] to a FortiSASE VPN tunnel to secure their traffic" over an "always-up VPN connection to ensure FortiSASE scans traffic to the internet." This mode also "supports configuring Zero Trust Network Access (ZTNA)." ZTNA is limited to **TCP-based applications** and "cannot support UDP-based applications and agentless remote users."
**Config touchpoints:** user provisioning + email invitations; endpoints "Download FortiClient … and connect to FortiClient Cloud using the code included in the invitation email," then FortiClient "connects to FortiClient Cloud to activate its FortiSASE subscription." Endpoint profiles control tunnel mode, ZTNA, split/full tunnel, and authentication (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/413962/forticlient-agent-based-mode-using-forticlient).
- *UNVERIFIED — needs confirmation:* the agent-based "Cloud Security" tunnel is documented in deployment guides as **SSL-VPN by default with IPsec as an option** (and 25.4 added IPsec-over-TCP/443), but the specific protocol/split-tunnel defaults were not directly confirmed on the agent-based-mode page; confirm in the SWG-with-VPN / SIA agent deployment guide before quoting to a customer.

### 3.2 Agentless On-Ramp (SWG explicit proxy & PAC)
**Who:** managed *and* unmanaged endpoints, BYOD, browser-only access — anywhere FortiClient can't or shouldn't be installed.
**Agent/device:** none. Browser/OS proxy settings only.
**How it connects:** SWG agentless mode uses a hosted **proxy auto-configuration (PAC) file**. "FortiSASE secure web gateway (SWG) agentless mode involves configuring and hosting a proxy autoconfiguration (PAC) file for endpoints to connect to the FortiSASE gateway." The PAC is JavaScript containing rules to route traffic to the proxy server or directly to the internet.
**Config touchpoints:** FortiSASE provides a preconfigured PAC hosted on the FortiSASE server; you can "customize the PAC to exclude the SSL VPN gateway and internal networks from being proxied," host the custom PAC on a customer-accessible server, and point endpoint browser/OS proxy settings at it. Explicit-proxy listener + authentication (SAML SSO) complete the path (Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/102431/pac-file-customization ; https://docs.fortinet.com/document/fortisase/26.1.99/mature-sia-agentless-swg-deployment-guide/515881/configuring-proxy-settings-on-endpoints).
- *Note:* 26.1 added a **Secure Browser extension** for unmanaged/contractor devices as another agentless option (see release notes corpus doc 03 §1.4).

### 3.3 Site-Based / Branch On-Ramp (BOR) / Thin-Edge
**Who:** whole branch sites; no per-endpoint agent or proxy config required. "FortiClient does not need to be installed on endpoints and web browser-based endpoints do not require explicit web proxy settings" — endpoints simply use the on-ramp device "as their default gateway."
**Agent/device:** a **certified IPsec device** at the branch (FortiGate; for **FortiSASE Mature, "the FortiGate is the only supported IPsec device that you can use for Branch On-ramp"**). The broader edge ecosystem documented includes **FortiExtender, FortiGate, and FortiAP**, and **FortiExtender 200F** specifically "can serve as an edge device managed by FortiSASE when … registered in the same FortiCloud account and licensed with a FortiSASE subscription license" (Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp ; https://docs.fortinet.com/document/fortisase/24.3.56/administration-guide/982382/thin-edge).

**How it connects (FortiGate edge):** native **IPsec dial-up tunnel** to a Branch On-ramp location. "The BOR node uses mode-config to dynamically assign tunnel interface IPs from a configured range to each connecting FortiGate," forming a hub-and-spoke topology with bidirectional traffic.

**Third-party / non-Fortinet IPsec devices:** supported as **IPsec dial-up clients requiring IKEv2**. "Since most lack mode-config support, each third-party device typically requires a dedicated tunnel with unique Local ID and Peer ID parameters for bidirectional communication." Configured via the **custom (third-party) device type** in *Edge Devices > SD-WAN On-Ramp* (Source: https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor).

**Scale limits (key SE numbers):**
- Per tenant: **minimum 2, maximum 20 BOR nodes** (= "A maximum of 20 On-Ramp locations are supported by FortiSASE in the cloud").
- Per BOR node: **1 Gbps shared bandwidth, up to 2000 branch connections**.
- Per tenant total: **up to 40,000 branch locations**.
- BOR nodes can be placed "in any FortiSASE PoP location," multiple in the same or different locations, and "a single branch location may connect to multiple BOR nodes for redundancy." The admin "decides in which FortiSASE location to deploy each BOR node."
- The BOR subscription license "restricts the number of On-Ramp locations that you can deploy based on the number of seats."
(Sources: https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor ; https://docs.fortinet.com/document/fortisase/25.3.67/feature-administration-guide/166485/deploying-an-branch-on-ramp-security-pop ; https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp).

**BGP / routing for BOR:** "BOR nodes will assume that the on-ramp branches have the same BGP ASN as defined on FortiSASE. In other words, only iBGP is supported between BOR and on-ramp branches," and BGP per-overlay is used for branch adjacency. Critically, **"BGP configuration is shared between the Branch On-ramp and Secure Private Access (SPA) features. You must configure the SPA network configuration first before deploying a Branch On-ramp location"** (Sources: https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor ; https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp).

**FortiSASE-managed thin edge vs FortiManager-managed.** Two operational models exist for the branch FortiGate/FortiExtender:
- **FortiSASE-managed** — the edge device is registered to the same FortiCloud account and licensed with a FortiSASE subscription; FortiSASE provisions/manages it directly (zero-touch via the FortiSASE portal). This is the FortiZTP-target-=-FortiSASE path (FortiAP / FortiExtender today; see automation corpus doc 02 §3.5).
- **FortiManager-managed** — the branch FortiGate is managed by FortiManager (SD-WAN templates, zero-touch provisioning) and merely forms the IPsec on-ramp tunnel to the BOR; security policy/config lives in FortiManager. See §6.
- *UNVERIFIED — needs confirmation:* the precise feature boundary (which exact config objects FortiSASE owns vs FortiManager owns) for a FortiManager-managed branch edge; confirm against the SIA Site-Based deployment guide and the FortiManager "Adding FortiSASE" topic before committing it to a customer design doc.

### 3.4 SPA Hubs (FortiGate Secure Private Access hubs + hub selection)
**Who:** organizations exposing private/data-center apps to FortiSASE remote users.
**Topology:** FortiSASE security PoPs are configured "as spokes in your hub-and-spoke network using the Secure Private Access page," connecting over IPsec VPN overlays + BGP to FortiGate SPA hub(s) (**up to 12 hubs**), with ADVPN for dynamic spoke-to-spoke tunnels (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/443423/spa).

**Routing design methods (Network > BGP):**
- **BGP per overlay** (default) and **BGP on loopback** (alternative).

**Hub selection methods:**
- **Hub health and priority** (service-connection priority).
- **BGP MED** — "When you set Hub Selection Method under Network > BGP to BGP MED and configure multiple BGP hubs, FortiSASE can use the multiexit discriminator (MED) BGP path attribute … to select a SPA hub for a given prefix," preferring **the hub advertising the lowest MED**. FortiSASE additionally supports **always-compare-med** (forces MED comparison across different ASes) and **deterministic-med** (groups routes by neighboring AS before best-path selection) for predictable selection when multiple hubs advertise the same prefix (Sources: https://docs.fortinet.com/document/fortisase/26.1.26/feature-administration-guide/711191/bgp-med-setting ; https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/128190/viewing-med-values-of-spa-routes).

---

## 4. Security PoP Architecture

**Two PoP infrastructures:**
- **Fortinet Cloud locations** — Fortinet-operated. The Reference Guide lists ~26 named locations: Ashburn VA, Auckland NZ, Bangalore, Burnaby, Dallas, Dubai (2), Frankfurt, Hong Kong, Istanbul, Johannesburg, Komagome (Japan), London, Madrid, Miami, Ottawa, Paris, Plano TX, Pune, San Jose, São Paulo, Singapore, Sydney, Tokyo, Toronto, Valbonne, Vancouver. Note Hong Kong and Dubai are excluded from the default UAE-onshore set per the data-center appendix.
- **Public Cloud locations** — **60+** regions documented spanning Americas/EMEA/APAC. 26.1 added Amsterdam, Ashburn, Chicago, Melbourne, Montreal, Osaka, Santiago, Stockholm. *UNVERIFIED — needs confirmation:* the specific public-cloud provider per region was not nameable from the cited pages; confirm via status.fortisase.com and the public-cloud appendix.
(Sources: https://docs.fortinet.com/document/fortisase/latest/reference-guide/663044/global-data-centers ; https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/751044/appendix-a-fortisase-data-centers).

**Provisioning footprint per tenant:** at setup, the admin configures **4 security PoPs + 1 log storage PoP**. Comprehensive tier unlocks unlimited Public Cloud selections and lets Public Cloud locations serve as **Analytics/Logging PoPs** (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/751044/appendix-a-fortisase-data-centers).

**Dedicated public IPs (customer-dedicated PoP behavior):** "FortiSASE assigns a dedicated public IP address per security PoP," enabling IP-based app access control, geo-restriction compliance, and third-party firewall allowlisting. **Advanced or Comprehensive remote-user subscriptions include a dedicated public IP per security PoP by default** (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/274515/dedicated-public-ip-addresses).

**Nearest-PoP selection (geo, not classic anycast):** "FortiSASE directs your endpoint to the closest security PoP based on the specific geolocation information of your endpoint's public IP address" — i.e., the egress public IP. For accurate selection, "use a resolving name server which implements the Extension Mechanisms for DNS (EDNS) Client Subnet extension (ECS)," so the originating /24 is forwarded to the authoritative DNS. Selecting more PoPs "improves redundancy and lowers latency." Regional-compliance rules can override nearest-PoP; absent a match, "the remote user tries to connect to their closest FortiSASE security PoP." Mainland-China users connecting to a PoP outside the country "may encounter suboptimal performance" (Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/295668/pops ; https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/751044/appendix-a-fortisase-data-centers).

---

## 5. Endpoint & Identity

**FortiClient agent + EMS-in-the-cloud.** FortiClient is managed by **FortiClient Cloud** (the cloud EMS embedded in FortiSASE). Onboarding flow: admin provisions users and emails **invitations**; the user downloads FortiClient and connects to FortiClient Cloud "using the code included in the invitation email" (the FortiSASE invitation code), which "activate[s] its FortiSASE subscription" (Source: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/413962/forticlient-agent-based-mode-using-forticlient).

**SAML / SSO IdP integration.** FortiSASE acts as a SAML **Service Provider**. Enable the SAML server under **Access & Authentication > Single Sign-On** and enter IdP settings under Identity Provider Configuration. Documented IdPs include **FortiAuthenticator** (on-prem and Cloud, the latter also as an **IdP proxy** enforcing MFA) and **Microsoft Entra ID** (via FortiAuthenticator Cloud as SAML IdP proxy). Remote auth methods such as **LDAP** are also supported. 25.4 added **SCIM** auto user provisioning (select availability) and **ZTNA auto OAuth login for Entra ID** (Sources: https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/912309/configuring-fortisase-with-fortiauthenticator-as-saml-idp-for-sso ; https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/338285/configuring-fortisase-with-fortiauthenticator-cloud-as-saml-idp-proxy-for-entra-id-sso).

**FIDO2 for agent tunnels.** FortiSASE supports **FIDO2 authentication for FortiClient agent tunnels**, configurable in Endpoint profiles for the **FortiSASE Cloud Security tunnel and custom tunnels** when "Authenticate with SSO" and "Use FortiClient built-in browser for SAML authentication" are enabled. Caveat: for SSL tunnels, "Allow FIDO authentication" restricts the method **only for FortiClient macOS endpoints**; for **Windows endpoints, FIDO2 must also be configured in the IdP** (e.g., Entra ID enterprise application) (Sources: https://docs.fortinet.com/document/fortisase/26.1.107/feature-release-notes/661728/whats-new ; https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/137493/custom-tunnels).

---

## 6. Where FortiManager / FortiGate / FortiAnalyzer Fit

**FortiManager co-management of FortiSASE.** FortiSASE can be onboarded to FortiManager (documented in FortiManager 7.6.x, *Device Manager > Adding FortiSASE*). Key constraints:
- **Only one FortiSASE can be onboarded per FortiManager.**
- Onboarding creates a **FortiSASE Connector** for FM↔FortiSASE communication.
- **Central management is one-way: configuration synchronizes from FortiManager → FortiSASE only** (Source: https://docs.fortinet.com/document/fortimanager/7.6.4/administration-guide/907875/adding-fortisase). Note FortiManager **7.4.4+** can sync Security Profiles, Users, Groups and Firewall Objects with FortiSASE (see licensing corpus doc 03 §4.2).

**FortiGate / SD-WAN.** FortiManager's SD-WAN pane manages SD-WAN on FortiManager-managed FortiGates, deploying "a single SD-WAN template … across multiple FortiGate devices" for zero-touch. This is the path for **FortiManager-managed branch edges** that form the IPsec on-ramp into a FortiSASE BOR (versus FortiSASE-managed thin edges provisioned from the FortiSASE portal). The SPA/SD-WAN hub side is also FortiManager-friendly — there is a dedicated "Configuring a new FortiGate SD-WAN enterprise deployment using FortiManager" guide for SPA (Sources: https://docs.fortinet.com/document/fortimanager/7.4.0/new-features/399767/sd-wan ; https://docs.fortinet.com/document/fortisase/25.2.30/spa-with-a-fortigate-sd-wan-deployment-guide/293222/configuring-a-new-fortigate-sd-wan-enterprise-deployment-using-fortimanager).

**FortiAnalyzer / logging & analytics.** FortiSASE allocates a dedicated **log storage PoP** at provisioning, and Comprehensive tier allows Public Cloud locations as **Analytics/Logging PoPs**. In the broader Fabric, FortiAnalyzer (or FortiAnalyzer Cloud / FortiGate Cloud) is the logging/analytics component, and FortiManager can also manage FortiAnalyzer devices.
- *UNVERIFIED — needs confirmation:* whether FortiSASE security-PoP traffic logs can be streamed to a customer-owned external FortiAnalyzer (vs only the FortiSASE-hosted analytics PoP); confirm in the FortiSASE log-settings / external-connector documentation.

---

## Quick-Reference: On-Ramp Decision Matrix

| On-ramp | Endpoint requirement | Connectivity | Primary use case | Key limits / notes |
|---|---|---|---|---|
| **Agent-based** | FortiClient + FortiClient Cloud | Always-on VPN tunnel (Cloud Security tunnel); ZTNA optional | Managed remote users; full SIA + SPA(ZTNA) + SSA | ZTNA = TCP apps only, agent required |
| **Agentless (SWG)** | None (browser/OS proxy + PAC) or Secure Browser ext | Explicit proxy via PAC file | Unmanaged/BYOD; web SIA + inline-CASB | No ZTNA; web/proxy traffic only |
| **Branch On-ramp (site/thin-edge)** | FortiGate (Mature: FortiGate only) / FortiExtender / FortiAP; or 3rd-party IPsec | IPsec dial-up + iBGP to BOR node | Whole-site, agentless | 2–20 BOR nodes/tenant; 1 Gbps & 2000 branches/node; 40,000/tenant; **SPA BGP config must exist first** |
| **SPA hub** | FortiGate SPA hub(s) | PoPs as spokes, IPsec overlays + BGP/ADVPN | Private/DC app access | Up to 12 hubs; hub selection via health/priority or BGP MED |

---

## Sources

Version applicability noted per link. "latest" tracks the current Mature/Feature release; specific version numbers reflect the page captured.

- [SASE architecture — Concept Guide 25.3.112](https://docs.fortinet.com/document/fortisase/25.3.112/concept-guide/832511/sase-architecture)
- [Technology used — Architecture Guide 26.1.107](https://docs.fortinet.com/document/fortisase/26.1.107/architecture-guide/87005/technology-used)
- [Site-based remote users using Branch On-ramp — Architecture Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/213023/site-based-remote-users-using-branch-on-ramp)
- [Branch On-Ramp (BOR) — Unified SASE for MSSP Architecture Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/unified-sase-for-mssp-architecture-guide/438696/branch-on-ramp-bor)
- [Deploying a Branch On-ramp security PoP — Feature Admin Guide 25.3.67](https://docs.fortinet.com/document/fortisase/25.3.67/feature-administration-guide/166485/deploying-an-branch-on-ramp-security-pop)
- [SD-WAN On-Ramp — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/213023/sd-wan-on-ramp)
- [SPA — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/443423/spa)
- [BGP MED Setting — Feature Admin Guide 26.1.26](https://docs.fortinet.com/document/fortisase/26.1.26/feature-administration-guide/711191/bgp-med-setting)
- [Viewing MED values of SPA routes — Feature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/128190/viewing-med-values-of-spa-routes)
- [FortiClient agent-based mode — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/413962/forticlient-agent-based-mode-using-forticlient)
- [PAC file customization — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/102431/pac-file-customization)
- [Configuring proxy settings on endpoints — Mature SIA Agentless SWG Deployment 26.1.99](https://docs.fortinet.com/document/fortisase/26.1.99/mature-sia-agentless-swg-deployment-guide/515881/configuring-proxy-settings-on-endpoints)
- [SSA using FortiSASE Inline-CASB — Architecture Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/architecture-guide/770469/ssa-using-fortisase-inline-casb)
- [Thin edge / FortiExtender LAN Extension — Admin Guide 24.3.56](https://docs.fortinet.com/document/fortisase/24.3.56/administration-guide/982382/thin-edge)
- [Appendix A — FortiSASE data centers — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/751044/appendix-a-fortisase-data-centers)
- [Global data centers — Reference Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/reference-guide/663044/global-data-centers)
- [PoPs — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/295668/pops)
- [Dedicated public IP addresses — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/274515/dedicated-public-ip-addresses)
- [Configuring FortiAuthenticator as SAML IdP for SSO — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/912309/configuring-fortisase-with-fortiauthenticator-as-saml-idp-for-sso)
- [FortiAuthenticator Cloud as IdP proxy for Entra ID SSO — Mature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/mature-administration-guide/338285/configuring-fortisase-with-fortiauthenticator-cloud-as-saml-idp-proxy-for-entra-id-sso)
- [What's new — Feature Release Notes 26.1.107](https://docs.fortinet.com/document/fortisase/26.1.107/feature-release-notes/661728/whats-new)
- [Custom tunnels — Feature Admin Guide (latest)](https://docs.fortinet.com/document/fortisase/latest/feature-administration-guide/137493/custom-tunnels)
- [Adding FortiSASE — FortiManager 7.6.4 Admin Guide](https://docs.fortinet.com/document/fortimanager/7.6.4/administration-guide/907875/adding-fortisase)
- [SD-WAN — FortiManager 7.4.0 New Features](https://docs.fortinet.com/document/fortimanager/7.4.0/new-features/399767/sd-wan)
- [SPA with FortiGate SD-WAN using FortiManager — Deployment Guide 25.2.30](https://docs.fortinet.com/document/fortisase/25.2.30/spa-with-a-fortigate-sd-wan-deployment-guide/293222/configuring-a-new-fortigate-sd-wan-enterprise-deployment-using-fortimanager)
- [FortiSASE product page](https://www.fortinet.com/products/sase)

**Items flagged UNVERIFIED (need SE confirmation before customer use):** agent-based tunnel default protocol/split-tunnel; exact FortiSASE-managed vs FortiManager-managed config-ownership boundary for branch edges; public-cloud provider names per PoP region; ability to stream FortiSASE PoP logs to a customer-owned external FortiAnalyzer.
