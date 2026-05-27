# Somni HUD — Even Realities G2 Plugin Design

> **Date**: 2026-05-27
> **Author**: Gerardo Palacios / Somni Labs
> **Status**: Draft
> **Scope**: A single Even Hub plugin for the Even Realities G2 smart glasses that acts as a unified Somni Labs command center — home control, 3D printer monitoring, Kubernetes cluster health, Claude Code terminal, and direct agent access (Hermes, OpenClaw).

---

## 1. Problem

The Even Realities G2 glasses ship with a Claude Code terminal integration that works well but has a critical limitation: it must be toggled from the phone app and cannot be activated from the glasses HUD. Additionally, there is no way to access the broader Somni Labs ecosystem (Home Assistant, Moonraker, cluster monitoring, Hermes, OpenClaw) from the glasses.

The goal is a single, private plugin — sideloaded via QR, never published to the public Even Hub store — that puts the entire Somni Labs operations on the glasses as a touch-navigable HUD.

## 2. Hardware & Platform Constraints

| Constraint | Value |
|---|---|
| Display | 576 x 288 px per eye, 4-bit greyscale (16 shades of green) |
| Input | Temple touchpads (tap, double-tap, swipe), optional R1 ring (click, scroll, double-click) |
| Audio | PCM 16kHz mono 16-bit microphone, requires `g2-microphone` permission |
| No camera | Privacy-first — no visual input |
| No speaker | All output is visual on the display |
| Runtime | Web app in phone WebView (Chromium/Android, WKWebView/iOS) |
| SDK | `@evenrealities/even_hub_sdk` v0.0.10 |
| Display limits | Max 4 image containers + 8 other containers per page |
| Text limits | 1,000 chars for `createStartUpPageContainer`, 2,000 chars for `textContainerUpgrade` |
| Image limits | Max 200x100 px, PNG/BMP binary, max 4 per page, no concurrent transmissions |
| Network | WebView respects `app.json` network whitelist; does not bypass CORS |

## 3. Architecture

### 3.1 System Overview

```
G2 Glasses (display + input only)
    | BLE 5.2
Phone WebView (somni-hud plugin)
    | HTTP/WS over Tailscale mesh
+---+-------------------------------------------+
|  Home Assistant API    (entity state, services) |
|  Moonraker API         (printer status, control)|
|  even-terminal pod     (Claude Code REST + WS)  |
|  Hermes API            (direct chat endpoint)   |
|  OpenClaw API          (direct chat endpoint)   |
|  Prometheus            (cluster metrics)         |
|  ArgoCD API            (app sync status)         |
+-------------------------------------------------+
```

**Key architectural decision:** No middleman. Each backend is called directly from the plugin over the Tailscale mesh. SomniMCP is not in the data path. The plugin is a thin client — all intelligence lives in the existing backends.

**Rationale:** Hermes has conversation-handling issues when routed through SomniMCP. Claude Code has a specific terminal protocol that even-terminal already handles. Going direct avoids routing quirks and keeps each connection simple.

### 3.2 Runtime Model

The plugin's TypeScript code executes in the phone's WebView. It communicates with the glasses via the Even Hub SDK bridge:

- **Outbound (app -> glasses):** `bridge.callEvenApp(method, params)` through the WebView bridge, then BLE to glasses
- **Inbound (glasses -> app):** User interactions travel via BLE to phone, then trigger `window._listenEvenAppMessage(...)` callbacks

App logic does not run on the glasses. The glasses handle only UI rendering and input event generation.

### 3.3 Network Access

All backend services are reachable via Tailscale mesh networking. If a service is available on the local LAN, it is available over Tailscale from anywhere. No VPN configuration or port forwarding required.

The `app.json` manifest must include a network whitelist covering all Tailscale endpoint hostnames/IPs.

## 4. Navigation Model

### 4.1 Interaction Paradigm

**Touch-first.** All navigation (grid selection, section switching, list scrolling, entity toggling) is done via temple touchpads and R1 ring. Voice input is activated only within agent conversational screens (Claude Code, Hermes, OpenClaw).

### 4.2 Screen Flow

```
Grid Home (5 tiles with live status)
  |
  | tap tile
  v
Full-Screen Card (that section)
  |
  | swipe left/right --> adjacent section card
  | double-tap ---------> back to Grid Home
  |
  | (in agent screens only)
  | tap to activate mic --> voice input --> send to agent
```

### 4.3 Navigation State Machine

States:
- `GRID` — Home grid visible, highlight movable between tiles
- `CARD` — Full-screen section card visible, swipe navigates laterally
- `AGENT` — Conversational screen (subset of CARD for terminal/agents sections)
- `SETUP` — First-run configuration screen

Transitions:
- `GRID` + tap -> `CARD` (selected section)
- `CARD` + swipe left -> `CARD` (previous section, wraps around)
- `CARD` + swipe right -> `CARD` (next section, wraps around)
- `CARD` + double-tap -> `GRID`
- `CARD` (agent section) + tap -> `AGENT` (mic activation)
- `AGENT` + double-tap -> `CARD`
- Boot + no config -> `SETUP`
- Boot + config exists -> `GRID`

Section order for lateral swiping: Home -> Printer -> Cluster -> Claude Code -> Agents (wraps)

## 5. Screen Definitions

### 5.1 Grid Home Screen

The launcher. Displays all 5 sections as tiles with live status summaries.

```
+---------------+---------------+---------------+
|   Home        |   Printer     |   Cluster     |
|  3 on  72F    |  67%  2h14m   |  72/72 synced |
+---------------+---------------+---------------+
|   Claude      |   Agents      |               |
|   idle        |   3 online    |               |
+---------------+---------------+---------------+
```

- R1 ring scroll or temple taps move the highlight between tiles
- Tap on highlighted tile enters that section
- Status badges update via polling (intervals per section)
- Each tile shows a 1-line status summary fetched from its backend

### 5.2 Home Screen (Home Assistant)

A scrollable list of frequently-used HA entities.

**Content:**
- Configurable list of 10-15 entities (defined in config)
- Each row: entity friendly name + current state (on/off, temperature, locked/unlocked)
- Grouped by room or entity type (configurable)

**Interactions:**
- Scroll up/down through the list (R1 ring or temple swipe)
- Tap to toggle (lights, switches, locks) or view detail (climate, sensors)
- Toggle sends `POST /api/services/{domain}/{service}` to HA

**Not a goal:** This is not a full somni-home dashboard replacement. It covers the 10-15 entities you actually control daily.

### 5.3 Printer Screen (Moonraker)

A single status card for the QIDI Q2.

**Content:**
- Current file name (truncated to fit)
- Progress: text-based bar + percentage (`████████░░ 67%`)
- Time remaining (estimated)
- Hotend temperature / target
- Bed temperature / target
- Printer state: idle / printing / paused / error / offline

**Interactions:**
- Tap to pause (if printing) or resume (if paused)
- Confirmation prompt before cancel (if implemented)

**Data source:** `GET /printer/objects/query?print_stats&heater_bed&extruder` — single Moonraker call returns all needed data.

### 5.4 Cluster Screen

Compact read-only health overview.

**Content:**
- ArgoCD sync: `X/Y apps synced` + list of any out-of-sync apps
- Node status: node names + ready/not-ready
- Problem pods: any in CrashLoopBackOff, Pending, or Failed (count + names)
- Active alerts: count of firing Prometheus/Grafana alerts

**Data sources:**
- Prometheus: instant query for node count, pod phase summary, firing alerts
- ArgoCD API: `GET /api/v1/applications` for sync status

**Interactions:** Read-only. Scroll to see full list if it overflows.

### 5.5 Claude Code Terminal

Interactive conversational screen connected to the even-terminal pod.

**Content:**
- Scrollable conversation history (most recent at bottom)
- Each message labeled: `You:` or `Claude:`
- Streaming responses render incrementally as chunks arrive

**Interactions:**
- Tap to activate microphone -> ASR captures speech -> text sent to even-terminal
- Response streams back via WebSocket and renders as scrollable text
- Swipe up/down to scroll through conversation history
- Double-tap to exit back to grid

**Protocol:**
- REST: `GET /api/sessions?provider=claude` (list sessions), `POST /api/conversations` (new session), `POST /api/messages` (send)
- WebSocket: persistent connection for streaming responses
- Auth: token header (stored in config)

### 5.6 Agents Screen

Two-level screen: agent picker -> conversational UI.

**Level 1 — Agent Picker:**
```
Hermes        [online]
OpenClaw      [online]
Claude Code   [idle]
```

- Scrollable list of available agents
- Each row shows agent name + connection status
- Status determined by a lightweight health check to each endpoint
- Tap to enter conversation with that agent

**Level 2 — Agent Conversation:**
- Identical layout to the Claude Code terminal screen
- Tap to activate mic, speak, see response
- Each agent maintains its own conversation state in memory
- Double-tap returns to agent picker (not grid — one level up)
- Double-tap from agent picker returns to grid

**Routing:**
- Claude Code -> even-terminal pod (REST + WS, same as terminal screen but accessed from agent picker)
- Hermes -> Hermes direct API endpoint
- OpenClaw -> OpenClaw direct API endpoint

## 6. Data Layer

### 6.1 API Clients

Each backend gets a dedicated client class. All clients follow a common interface:

```typescript
interface SectionClient {
  getStatusSummary(): Promise<string>  // One-line summary for grid tile
  getFullData(): Promise<SectionData>  // Full data for the card screen
  isHealthy(): Promise<boolean>        // Health check for grid badge
}
```

Agent clients extend this with conversational methods:

```typescript
interface AgentClient extends SectionClient {
  sendMessage(text: string): Promise<void>
  onResponse(callback: (chunk: string) => void): void
  getHistory(): Message[]
}
```

### 6.2 Client Specifications

**Home Assistant Client:**
- Endpoint: HA instance URL over Tailscale
- Auth: Long-lived access token in `Authorization: Bearer` header
- Grid summary: fetch key entities, format as "X on, Y°F, alarm state"
- Full screen: fetch configurable entity list, render as scrollable list
- Toggle: `POST /api/services/{domain}/{service}` with entity_id body

**Moonraker Client:**
- Endpoint: Moonraker URL over Tailscale (default `http://192.168.1.15:7125`)
- Auth: None (Moonraker default config)
- Grid summary: progress percentage + time remaining
- Full screen: all print stats, temperatures, state
- Control: `POST /printer/print/pause`, `/printer/print/resume`

**Even-Terminal Client:**
- Endpoint: even-terminal pod, port 3456
- Auth: Token in request header
- Sessions: `GET /api/sessions?provider=claude`
- New conversation: `POST /api/conversations`
- Send message: `POST /api/messages`
- Stream responses: WebSocket connection
- Grid summary: "idle" or "active session"

**Hermes Client:**
- Endpoint: Hermes direct API over Tailscale
- Auth: per Hermes requirements
- Chat: direct REST endpoint for sending messages
- Streaming: SSE or WebSocket per Hermes protocol
- Grid summary: online/offline status

**OpenClaw Client:**
- Endpoint: OpenClaw direct API over Tailscale
- Auth: per OpenClaw requirements
- Same conversational pattern as Hermes

**Prometheus Client:**
- Endpoint: Prometheus server over Tailscale (port 9090)
- Auth: None (internal service)
- Query: `GET /api/v1/query` with PromQL instant queries
- Queries needed:
  - Node count: `count(kube_node_info)`
  - Non-ready nodes: `kube_node_status_condition{condition="Ready",status="false"}`
  - Pod phase summary: `count by (phase) (kube_pod_status_phase)`
  - Firing alerts: `count(ALERTS{alertstate="firing"})`

**ArgoCD Client:**
- Endpoint: ArgoCD server over Tailscale
- Auth: ArgoCD API token in `Authorization: Bearer` header
- Applications: `GET /api/v1/applications`
- Parse response for sync status counts (Synced vs OutOfSync vs Unknown)

### 6.3 Polling Strategy

| Section | Interval (active screen) | Interval (grid badge) | Backoff on failure |
|---|---|---|---|
| Home (HA) | 5 seconds | 30 seconds | 5s -> 15s -> 30s -> 60s |
| Printer | 10 seconds | 30 seconds | 10s -> 30s -> 60s |
| Cluster | 30 seconds | 60 seconds | 30s -> 60s -> 120s |
| Agents | On-demand (health check on grid load) | 60 seconds | 60s -> 120s |

- When viewing a section's full-screen card, that section polls at its active rate
- When on the grid, all sections poll at their grid badge rate
- On failure, exponential backoff up to the max interval
- On success after failure, immediately revert to normal interval
- Stale data is always displayed with an age indicator rather than blank screen

## 7. Configuration & Auth

### 7.1 Storage

All configuration is stored in the Even Hub SDK's local storage — a string-based key-value store that persists across reboots. No credentials are hardcoded in the source.

### 7.2 Config Schema

```typescript
interface SomniHudConfig {
  ha: {
    url: string          // e.g., "https://ha.tail.net"
    token: string        // Long-lived access token
    entities: string[]   // Entity IDs to show on home screen
  }
  moonraker: {
    url: string          // e.g., "http://100.x.x.x:7125"
  }
  evenTerminal: {
    url: string          // e.g., "http://100.x.x.x:3456"
    token: string        // Auth token
  }
  hermes: {
    url: string
    token: string
  }
  openclaw: {
    url: string
    token: string
  }
  prometheus: {
    url: string          // e.g., "http://100.x.x.x:9090"
  }
  argocd: {
    url: string
    token: string
  }
  polling: {
    ha: number           // ms, default 5000
    printer: number      // ms, default 10000
    cluster: number      // ms, default 30000
    agents: number       // ms, default 60000
  }
}
```

### 7.3 First-Run Setup

1. Plugin boots, reads `somni-hud-config` key from SDK local storage
2. If missing or invalid, displays setup screen
3. Setup screen is a series of text prompts rendered on the glasses with phone-side text input via the WebView
4. User enters each endpoint URL and token
5. Config is serialized as JSON string and saved to SDK local storage
6. Plugin transitions to the grid home screen
7. Subsequent boots skip setup entirely

### 7.4 Config Updates

A hidden "Settings" option accessible from the grid (e.g., long-press on the grid screen or a 6th tile) allows re-entering setup to update endpoints or tokens.

## 8. Error Handling & Resilience

### 8.1 Per-Section Isolation

Every API call is wrapped in try/catch with a 5-second timeout. A failure in one section never affects another. If the printer is off, the home controls still work.

### 8.2 Failure States

| Scenario | Grid tile behavior | Card screen behavior |
|---|---|---|
| Backend unreachable | Badge shows `offline` | Shows "Last updated X min ago" with stale data |
| Backend returns error | Badge shows `error` | Shows error message + "tap to retry" |
| Timeout (>5s) | Uses last known data | Shows stale data with age indicator |
| First load, no data yet | Shows `loading...` | Shows loading indicator |

### 8.3 Agent Conversation Resilience

- WebSocket disconnect mid-conversation: show "Connection lost — tap to retry"
- Conversation history preserved in local memory (not just the WebSocket stream)
- Automatic reconnection with exponential backoff (1s -> 2s -> 4s -> 8s -> 16s max)
- Partial streamed responses are preserved (don't discard what's already rendered)

### 8.4 Startup Sequence

1. Plugin initializes SDK bridge (`waitForEvenAppBridge()`)
2. Load config from local storage
3. If no config -> SETUP screen
4. If config exists -> render grid immediately with "loading..." on all tiles
5. Fire all section health checks in parallel
6. As each responds, update its grid tile badge
7. Full grid populated within seconds, degraded gracefully for slow/offline backends

### 8.5 Grid Home is Always Safe

The grid screen renders purely from local state. Even if every backend is offline, you see 5 tiles with "offline" badges. Navigation always works. The plugin never shows a blank screen or a crash dialog.

## 9. Project Structure

```
somni-hud/
  package.json
  app.json                 # Even Hub manifest
  vite.config.ts
  tsconfig.json
  src/
    main.ts                # SDK init, router, polling orchestrator
    config.ts              # Config schema, load/save from SDK storage
    setup.ts               # First-run configuration screen
    types.ts               # Shared TypeScript types
    api/
      ha.ts                # Home Assistant REST client
      moonraker.ts         # Moonraker REST client
      even-terminal.ts     # Claude Code REST + WebSocket client
      hermes.ts            # Hermes REST client
      openclaw.ts          # OpenClaw REST client
      prometheus.ts        # Prometheus instant query client
      argocd.ts            # ArgoCD application list client
    screens/
      grid.ts              # Home grid (5 tiles, live status badges)
      home.ts              # HA entity list + toggle controls
      terminal.ts          # Claude Code conversational UI
      printer.ts           # Print status + pause/resume
      cluster.ts           # Nodes, pods, ArgoCD sync, alerts
      agents.ts            # Agent picker + conversational UI
    lib/
      nav.ts               # Navigation state machine
      display.ts           # Text/list/image container helpers
      polling.ts           # Polling manager with backoff
      audio.ts             # Mic activation + PCM stream helpers
```

### 9.1 `app.json` Manifest

```json
{
  "name": "Somni HUD",
  "version": "0.1.0",
  "description": "Somni Labs command center for Even G2",
  "permissions": ["g2-microphone"],
  "network": [
    "ha.tail.net",
    "100.*.*.*",
    "*.tail.net"
  ]
}
```

Network whitelist must cover all Tailscale endpoints. If Even Hub does not support wildcards or CIDR, each Tailscale IP must be listed individually. Verify wildcard support during implementation and fall back to explicit IPs if needed.

### 9.2 Toolchain

| Command | Purpose |
|---|---|
| `npm run dev` | Vite dev server with hot reload |
| `evenhub-simulator http://localhost:5173` | Desktop testing without glasses |
| `evenhub qr --url "http://<tailscale-ip>:5173"` | QR sideload to glasses |
| `npx evenhub pack` | Build `.ehpk` package |

### 9.3 Dependencies

- `@evenrealities/even_hub_sdk` — SDK bridge to glasses hardware
- `@evenrealities/evenhub-simulator` (dev) — Desktop simulator
- `@evenrealities/evenhub-cli` (dev) — QR generation and packaging
- `vite` — Build toolchain
- `typescript` — Type safety

No other runtime dependencies. All API clients are plain `fetch()` calls. No axios, no state management library, no UI framework.

## 10. Tech Stack Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | None (vanilla TS) | The display is 576x288 greyscale text. React/Vue add weight for zero benefit. |
| State management | Plain module-level variables | One user, one screen at a time, no shared reactive state needed. |
| API client | Native `fetch()` + `WebSocket` | No need for axios when every call is a simple REST request. |
| Build tool | Vite | Required by Even Hub ecosystem. Fast HMR for rapid iteration. |
| Testing | Vitest + evenhub-simulator | Unit tests for API clients and nav state machine. Manual testing via simulator and on-device. |

## 11. Future Extensions

Not in scope for v1, but the architecture supports:

- **Discord integration** — A 6th tile for Discord DMs or channel monitoring via Discord bot API
- **Calendar/schedule** — LifeOS today summary via SomniMCP's `lifeos_get_today_summary`
- **Notifications push** — HA events (doorbell, alarm trigger) pushed to glasses proactively rather than polled
- **Finance glance** — Quick spending summary from somni-finance
- **Omi memory search** — Voice query against Omi memories via SomniMCP

These can be added as new screen files + API clients without modifying the existing architecture.

## 12. Open Questions

1. **Hermes direct API protocol** — Need to verify the exact REST/WS endpoint for direct chat (not through SomniMCP). The `hermes_chat` MCP skill exists but we need the underlying HTTP API.
2. **OpenClaw direct API protocol** — Same as above for OpenClaw.
3. **Even Hub network whitelist syntax** — Need to confirm whether `app.json` supports wildcards or CIDR ranges for Tailscale IPs.
4. **ASR implementation** — The G2 mic provides raw PCM audio. Need to determine: does the SDK provide built-in ASR, or do we need to stream audio to a speech-to-text service (Whisper, Soniox, etc.)?
5. **Even-terminal WebSocket protocol** — Exact WS message format for streaming Claude responses needs verification during implementation.
