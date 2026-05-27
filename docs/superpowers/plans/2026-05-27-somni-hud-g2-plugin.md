# Somni HUD G2 Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single Even Hub plugin for Even Realities G2 smart glasses that acts as a unified Somni Labs command center — grid home screen with 5 tiles (Home, Printer, Cluster, Claude Code, Agents), touch-first navigation, direct API calls to backend services over Tailscale mesh.

**Architecture:** Vanilla TypeScript + Vite + `@evenrealities/even_hub_sdk`. No framework. Each backend gets a dedicated API client using native `fetch()`. Navigation is a state machine (GRID/CARD/AGENT/SETUP). All config stored in SDK local storage. The plugin runs in the phone's WebView and communicates with glasses via the SDK bridge.

**Tech Stack:** TypeScript, Vite, `@evenrealities/even_hub_sdk` v0.0.10, Vitest, native `fetch()` + `WebSocket`

**Spec:** `docs/superpowers/specs/2026-05-27-somni-hud-g2-plugin-design.md`

---

## File Map

```
somni-hud/
  package.json                  # Project config, scripts, dependencies
  app.json                      # Even Hub manifest (permissions, network whitelist)
  vite.config.ts                # Vite dev server config (host: true for LAN access)
  tsconfig.json                 # TypeScript strict config
  index.html                    # Entry HTML (loads src/main.ts)
  src/
    main.ts                     # SDK bridge init, config load, router bootstrap
    types.ts                    # All shared TypeScript interfaces
    config.ts                   # Config load/save from SDK local storage
    nav.ts                      # Navigation state machine (GRID/CARD/AGENT/SETUP)
    polling.ts                  # Polling manager with exponential backoff
    display.ts                  # SDK container helpers (text, list, page management)
    api/
      ha.ts                     # Home Assistant REST client
      moonraker.ts              # Moonraker REST client
      even-terminal.ts          # Claude Code REST + WebSocket client
      hermes.ts                 # Hermes /v1/chat/completions client
      openclaw.ts               # OpenClaw /v1/chat/completions client
      prometheus.ts             # Prometheus instant query client
      argocd.ts                 # ArgoCD application list client
    screens/
      setup.ts                  # First-run config entry screen
      grid.ts                   # Home grid (5 tiles with live status badges)
      home.ts                   # HA entity list + toggle controls
      printer.ts                # Moonraker print status + pause/resume
      cluster.ts                # K8s nodes, pods, ArgoCD sync, alerts
      terminal.ts               # Claude Code conversational screen
      agents.ts                 # Agent picker + conversational UI
  tests/
    nav.test.ts                 # Navigation state machine tests
    polling.test.ts             # Polling manager tests
    config.test.ts              # Config load/save tests
    api/
      ha.test.ts                # HA client tests
      moonraker.test.ts         # Moonraker client tests
      even-terminal.test.ts     # Even-terminal client tests
      hermes.test.ts            # Hermes client tests
      openclaw.test.ts          # OpenClaw client tests
      prometheus.test.ts        # Prometheus client tests
      argocd.test.ts            # ArgoCD client tests
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `somni-hud/package.json`
- Create: `somni-hud/app.json`
- Create: `somni-hud/vite.config.ts`
- Create: `somni-hud/tsconfig.json`
- Create: `somni-hud/index.html`
- Create: `somni-hud/src/main.ts`

- [ ] **Step 1: Create project directory**

The new project lives at the SomniApps level, alongside somni-home, SomniMCP, etc.

```bash
mkdir -p /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud/src
mkdir -p /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud/tests/api
```

- [ ] **Step 2: Create package.json**

Create `somni-hud/package.json`:

```json
{
  "name": "somni-hud",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "typecheck": "tsc --noEmit",
    "pack": "evenhub pack"
  },
  "dependencies": {
    "@evenrealities/even_hub_sdk": "^0.0.10"
  },
  "devDependencies": {
    "@evenrealities/evenhub-cli": "^0.1.12",
    "@evenrealities/evenhub-simulator": "^0.7.2",
    "typescript": "^5.5.0",
    "vite": "^6.0.0",
    "vitest": "^3.0.0"
  }
}
```

- [ ] **Step 3: Create app.json**

Create `somni-hud/app.json`:

```json
{
  "package_id": "io.somni-labs.hud",
  "edition": "202605",
  "name": "Somni HUD",
  "version": "0.1.0",
  "min_app_version": "2.0.0",
  "min_sdk_version": "0.0.10",
  "entrypoint": "index.html",
  "permissions": [
    {
      "name": "g2-microphone",
      "desc": "Capture audio for voice commands to Claude, Hermes, and OpenClaw agents."
    }
  ],
  "supported_languages": ["en"]
}
```

- [ ] **Step 4: Create vite.config.ts**

Create `somni-hud/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: true,
    port: 5173,
  },
  build: {
    target: 'esnext',
  },
  test: {
    globals: true,
    environment: 'node',
  },
})
```

- [ ] **Step 5: Create tsconfig.json**

Create `somni-hud/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "tests"]
}
```

- [ ] **Step 6: Create index.html**

Create `somni-hud/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Somni HUD</title>
</head>
<body>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 7: Create placeholder main.ts**

Create `somni-hud/src/main.ts`:

```typescript
import { waitForEvenAppBridge } from '@evenrealities/even_hub_sdk'

async function boot() {
  const bridge = await waitForEvenAppBridge()
  console.log('[somni-hud] bridge ready')
}

boot().catch(console.error)
```

- [ ] **Step 8: Install dependencies and verify build**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npm install
npx tsc --noEmit
```

Expected: clean install, no type errors.

- [ ] **Step 9: Initialize git and commit**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
git init
echo "node_modules/\ndist/\n.ehpk" > .gitignore
git add .
git commit -m "feat: scaffold somni-hud Even Hub plugin project"
```

---

## Task 2: Shared Types

**Files:**
- Create: `somni-hud/src/types.ts`

- [ ] **Step 1: Create types.ts with all shared interfaces**

Create `somni-hud/src/types.ts`:

```typescript
// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export interface SomniHudConfig {
  ha: {
    url: string
    token: string
    entities: string[]
  }
  moonraker: {
    url: string
  }
  evenTerminal: {
    url: string
    token: string
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
    url: string
  }
  argocd: {
    url: string
    token: string
  }
  polling: {
    ha: number
    printer: number
    cluster: number
    agents: number
  }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

export enum NavState {
  SETUP = 'SETUP',
  GRID = 'GRID',
  CARD = 'CARD',
  AGENT = 'AGENT',
}

export enum Section {
  HOME = 0,
  PRINTER = 1,
  CLUSTER = 2,
  TERMINAL = 3,
  AGENTS = 4,
}

export const SECTION_ORDER: Section[] = [
  Section.HOME,
  Section.PRINTER,
  Section.CLUSTER,
  Section.TERMINAL,
  Section.AGENTS,
]

export const SECTION_LABELS: Record<Section, string> = {
  [Section.HOME]: 'Home',
  [Section.PRINTER]: 'Printer',
  [Section.CLUSTER]: 'Cluster',
  [Section.TERMINAL]: 'Claude',
  [Section.AGENTS]: 'Agents',
}

// ---------------------------------------------------------------------------
// Section Data
// ---------------------------------------------------------------------------

export interface SectionStatus {
  summary: string
  healthy: boolean
  lastUpdated: number
}

export interface HaEntity {
  entity_id: string
  state: string
  attributes: {
    friendly_name?: string
    unit_of_measurement?: string
    [key: string]: unknown
  }
}

export interface PrinterData {
  state: 'idle' | 'printing' | 'paused' | 'error' | 'offline'
  filename: string
  progress: number
  timeRemaining: number
  hotendTemp: number
  hotendTarget: number
  bedTemp: number
  bedTarget: number
}

export interface ClusterData {
  nodeCount: number
  nodesReady: number
  podTotal: number
  podRunning: number
  podPending: number
  podFailed: number
  alertsFiring: number
  argoTotal: number
  argoSynced: number
  argoOutOfSync: string[]
}

// ---------------------------------------------------------------------------
// Agent / Conversation
// ---------------------------------------------------------------------------

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export enum AgentId {
  CLAUDE = 'claude',
  HERMES = 'hermes',
  OPENCLAW = 'openclaw',
}

export const AGENT_LABELS: Record<AgentId, string> = {
  [AgentId.CLAUDE]: 'Claude Code',
  [AgentId.HERMES]: 'Hermes',
  [AgentId.OPENCLAW]: 'OpenClaw',
}

export interface AgentStatus {
  id: AgentId
  label: string
  online: boolean
}

// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------

export interface PollHandle {
  start(): void
  stop(): void
  trigger(): Promise<void>
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/types.ts
git commit -m "feat: add shared TypeScript types for config, nav, sections, agents"
```

---

## Task 3: Config Module

**Files:**
- Create: `somni-hud/src/config.ts`
- Create: `somni-hud/tests/config.test.ts`

- [ ] **Step 1: Write failing tests for config load/save**

Create `somni-hud/tests/config.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { loadConfig, saveConfig, isConfigValid, DEFAULT_POLLING } from '../src/config.ts'

const mockBridge = {
  getLocalStorage: vi.fn(),
  setLocalStorage: vi.fn(),
}

describe('config', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('loadConfig', () => {
    it('returns null when no config stored', async () => {
      mockBridge.getLocalStorage.mockResolvedValue('')
      const result = await loadConfig(mockBridge as any)
      expect(result).toBeNull()
    })

    it('returns null for invalid JSON', async () => {
      mockBridge.getLocalStorage.mockResolvedValue('not json')
      const result = await loadConfig(mockBridge as any)
      expect(result).toBeNull()
    })

    it('returns parsed config for valid JSON', async () => {
      const config = {
        ha: { url: 'http://ha.local', token: 'tok', entities: ['light.desk'] },
        moonraker: { url: 'http://printer.local:7125' },
        evenTerminal: { url: 'http://et.local:3456', token: 'tok' },
        hermes: { url: 'http://hermes.local:8642', token: 'tok' },
        openclaw: { url: 'http://oc.local:18789', token: 'tok' },
        prometheus: { url: 'http://prom.local:9090' },
        argocd: { url: 'http://argocd.local', token: 'tok' },
        polling: { ha: 5000, printer: 10000, cluster: 30000, agents: 60000 },
      }
      mockBridge.getLocalStorage.mockResolvedValue(JSON.stringify(config))
      const result = await loadConfig(mockBridge as any)
      expect(result).toEqual(config)
    })
  })

  describe('saveConfig', () => {
    it('serializes and stores config', async () => {
      mockBridge.setLocalStorage.mockResolvedValue(true)
      const config = {
        ha: { url: 'http://ha.local', token: 'tok', entities: [] },
        moonraker: { url: 'http://printer.local:7125' },
        evenTerminal: { url: 'http://et.local:3456', token: 'tok' },
        hermes: { url: 'http://hermes.local:8642', token: 'tok' },
        openclaw: { url: 'http://oc.local:18789', token: 'tok' },
        prometheus: { url: 'http://prom.local:9090' },
        argocd: { url: 'http://argocd.local', token: 'tok' },
        polling: { ha: 5000, printer: 10000, cluster: 30000, agents: 60000 },
      }
      await saveConfig(mockBridge as any, config)
      expect(mockBridge.setLocalStorage).toHaveBeenCalledWith(
        'somni-hud-config',
        JSON.stringify(config)
      )
    })
  })

  describe('isConfigValid', () => {
    it('returns false for null', () => {
      expect(isConfigValid(null)).toBe(false)
    })

    it('returns false when ha.url is missing', () => {
      expect(isConfigValid({ ha: { url: '', token: 'x', entities: [] } } as any)).toBe(false)
    })

    it('returns true for a minimal valid config', () => {
      const config = {
        ha: { url: 'http://ha', token: 'x', entities: [] },
        moonraker: { url: 'http://mr' },
        evenTerminal: { url: 'http://et', token: 'x' },
        hermes: { url: 'http://h', token: 'x' },
        openclaw: { url: 'http://oc', token: 'x' },
        prometheus: { url: 'http://p' },
        argocd: { url: 'http://a', token: 'x' },
        polling: { ha: 5000, printer: 10000, cluster: 30000, agents: 60000 },
      }
      expect(isConfigValid(config)).toBe(true)
    })
  })

  describe('DEFAULT_POLLING', () => {
    it('has expected default intervals', () => {
      expect(DEFAULT_POLLING).toEqual({
        ha: 5000,
        printer: 10000,
        cluster: 30000,
        agents: 60000,
      })
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx vitest run tests/config.test.ts
```

Expected: FAIL — modules not found.

- [ ] **Step 3: Implement config module**

Create `somni-hud/src/config.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import type { SomniHudConfig } from './types.ts'

const CONFIG_KEY = 'somni-hud-config'

export const DEFAULT_POLLING = {
  ha: 5000,
  printer: 10000,
  cluster: 30000,
  agents: 60000,
} as const

export async function loadConfig(bridge: EvenAppBridge): Promise<SomniHudConfig | null> {
  try {
    const raw = await bridge.getLocalStorage(CONFIG_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return isConfigValid(parsed) ? parsed : null
  } catch {
    return null
  }
}

export async function saveConfig(bridge: EvenAppBridge, config: SomniHudConfig): Promise<void> {
  await bridge.setLocalStorage(CONFIG_KEY, JSON.stringify(config))
}

export function isConfigValid(config: unknown): config is SomniHudConfig {
  if (!config || typeof config !== 'object') return false
  const c = config as Record<string, unknown>

  const hasUrl = (key: string): boolean => {
    const section = c[key] as Record<string, unknown> | undefined
    return typeof section?.url === 'string' && section.url.length > 0
  }

  const hasUrlAndToken = (key: string): boolean => {
    const section = c[key] as Record<string, unknown> | undefined
    return hasUrl(key) && typeof section?.token === 'string' && section!.token.length > 0
  }

  return (
    hasUrlAndToken('ha') &&
    hasUrl('moonraker') &&
    hasUrlAndToken('evenTerminal') &&
    hasUrlAndToken('hermes') &&
    hasUrlAndToken('openclaw') &&
    hasUrl('prometheus') &&
    hasUrlAndToken('argocd') &&
    typeof (c.polling as Record<string, unknown>)?.ha === 'number'
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx vitest run tests/config.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/config.ts tests/config.test.ts
git commit -m "feat: add config module with load/save/validate from SDK local storage"
```

---

## Task 4: Navigation State Machine

**Files:**
- Create: `somni-hud/src/nav.ts`
- Create: `somni-hud/tests/nav.test.ts`

- [ ] **Step 1: Write failing tests for navigation state machine**

Create `somni-hud/tests/nav.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { NavMachine } from '../src/nav.ts'
import { NavState, Section } from '../src/types.ts'

describe('NavMachine', () => {
  let nav: NavMachine

  beforeEach(() => {
    nav = new NavMachine()
  })

  describe('initial state', () => {
    it('starts in GRID state', () => {
      expect(nav.state).toBe(NavState.GRID)
    })

    it('starts with HOME section', () => {
      expect(nav.activeSection).toBe(Section.HOME)
    })

    it('starts with gridHighlight at 0', () => {
      expect(nav.gridHighlight).toBe(0)
    })
  })

  describe('GRID -> CARD', () => {
    it('tap enters CARD for highlighted section', () => {
      nav.gridHighlight = 2
      nav.tap()
      expect(nav.state).toBe(NavState.CARD)
      expect(nav.activeSection).toBe(Section.CLUSTER)
    })
  })

  describe('CARD lateral swiping', () => {
    it('swipe right advances to next section', () => {
      nav.tap() // enter CARD for HOME (0)
      nav.swipeRight()
      expect(nav.activeSection).toBe(Section.PRINTER)
    })

    it('swipe left goes to previous section', () => {
      nav.tap() // enter CARD for HOME (0)
      nav.swipeLeft()
      expect(nav.activeSection).toBe(Section.AGENTS) // wraps around
    })

    it('swipe right wraps from AGENTS to HOME', () => {
      nav.gridHighlight = 4
      nav.tap() // enter CARD for AGENTS
      nav.swipeRight()
      expect(nav.activeSection).toBe(Section.HOME)
    })
  })

  describe('CARD -> GRID', () => {
    it('double-tap returns to GRID', () => {
      nav.tap()
      nav.doubleTap()
      expect(nav.state).toBe(NavState.GRID)
    })

    it('preserves gridHighlight matching the active section', () => {
      nav.gridHighlight = 2
      nav.tap()
      nav.swipeRight() // CLUSTER -> TERMINAL
      nav.doubleTap()
      expect(nav.gridHighlight).toBe(3) // TERMINAL index
    })
  })

  describe('CARD -> AGENT (agent sections)', () => {
    it('tap in TERMINAL card enters AGENT state', () => {
      nav.gridHighlight = 3
      nav.tap() // CARD for TERMINAL
      nav.tap() // activate AGENT
      expect(nav.state).toBe(NavState.AGENT)
    })

    it('tap in non-agent CARD does not enter AGENT', () => {
      nav.gridHighlight = 0
      nav.tap() // CARD for HOME
      nav.tap() // should NOT enter AGENT
      expect(nav.state).toBe(NavState.CARD)
    })
  })

  describe('AGENT -> CARD', () => {
    it('double-tap from AGENT returns to CARD', () => {
      nav.gridHighlight = 3
      nav.tap() // CARD
      nav.tap() // AGENT
      nav.doubleTap()
      expect(nav.state).toBe(NavState.CARD)
      expect(nav.activeSection).toBe(Section.TERMINAL)
    })
  })

  describe('GRID highlight movement', () => {
    it('scrollUp decrements gridHighlight', () => {
      nav.gridHighlight = 2
      nav.scrollUp()
      expect(nav.gridHighlight).toBe(1)
    })

    it('scrollDown increments gridHighlight', () => {
      nav.gridHighlight = 2
      nav.scrollDown()
      expect(nav.gridHighlight).toBe(3)
    })

    it('scrollUp wraps from 0 to 4', () => {
      nav.gridHighlight = 0
      nav.scrollUp()
      expect(nav.gridHighlight).toBe(4)
    })

    it('scrollDown wraps from 4 to 0', () => {
      nav.gridHighlight = 4
      nav.scrollDown()
      expect(nav.gridHighlight).toBe(0)
    })

    it('scroll in CARD state is ignored', () => {
      nav.tap()
      nav.scrollUp()
      expect(nav.state).toBe(NavState.CARD)
    })
  })

  describe('SETUP state', () => {
    it('can be set to SETUP', () => {
      nav.enterSetup()
      expect(nav.state).toBe(NavState.SETUP)
    })

    it('exitSetup goes to GRID', () => {
      nav.enterSetup()
      nav.exitSetup()
      expect(nav.state).toBe(NavState.GRID)
    })
  })

  describe('isAgentSection', () => {
    it('TERMINAL is an agent section', () => {
      expect(NavMachine.isAgentSection(Section.TERMINAL)).toBe(true)
    })

    it('AGENTS is an agent section', () => {
      expect(NavMachine.isAgentSection(Section.AGENTS)).toBe(true)
    })

    it('HOME is not an agent section', () => {
      expect(NavMachine.isAgentSection(Section.HOME)).toBe(false)
    })

    it('PRINTER is not an agent section', () => {
      expect(NavMachine.isAgentSection(Section.PRINTER)).toBe(false)
    })

    it('CLUSTER is not an agent section', () => {
      expect(NavMachine.isAgentSection(Section.CLUSTER)).toBe(false)
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx vitest run tests/nav.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement navigation state machine**

Create `somni-hud/src/nav.ts`:

```typescript
import { NavState, Section, SECTION_ORDER } from './types.ts'

const SECTION_COUNT = SECTION_ORDER.length

export class NavMachine {
  state: NavState = NavState.GRID
  activeSection: Section = Section.HOME
  gridHighlight = 0

  static isAgentSection(section: Section): boolean {
    return section === Section.TERMINAL || section === Section.AGENTS
  }

  tap(): void {
    if (this.state === NavState.GRID) {
      this.activeSection = SECTION_ORDER[this.gridHighlight]!
      this.state = NavState.CARD
      return
    }
    if (this.state === NavState.CARD && NavMachine.isAgentSection(this.activeSection)) {
      this.state = NavState.AGENT
      return
    }
  }

  doubleTap(): void {
    if (this.state === NavState.AGENT) {
      this.state = NavState.CARD
      return
    }
    if (this.state === NavState.CARD) {
      this.gridHighlight = SECTION_ORDER.indexOf(this.activeSection)
      this.state = NavState.GRID
      return
    }
  }

  swipeRight(): void {
    if (this.state !== NavState.CARD) return
    const idx = SECTION_ORDER.indexOf(this.activeSection)
    this.activeSection = SECTION_ORDER[(idx + 1) % SECTION_COUNT]!
  }

  swipeLeft(): void {
    if (this.state !== NavState.CARD) return
    const idx = SECTION_ORDER.indexOf(this.activeSection)
    this.activeSection = SECTION_ORDER[(idx - 1 + SECTION_COUNT) % SECTION_COUNT]!
  }

  scrollUp(): void {
    if (this.state !== NavState.GRID) return
    this.gridHighlight = (this.gridHighlight - 1 + SECTION_COUNT) % SECTION_COUNT
  }

  scrollDown(): void {
    if (this.state !== NavState.GRID) return
    this.gridHighlight = (this.gridHighlight + 1) % SECTION_COUNT
  }

  enterSetup(): void {
    this.state = NavState.SETUP
  }

  exitSetup(): void {
    this.state = NavState.GRID
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx vitest run tests/nav.test.ts
```

Expected: all 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/nav.ts tests/nav.test.ts
git commit -m "feat: add navigation state machine (GRID/CARD/AGENT/SETUP)"
```

---

## Task 5: Polling Manager

**Files:**
- Create: `somni-hud/src/polling.ts`
- Create: `somni-hud/tests/polling.test.ts`

- [ ] **Step 1: Write failing tests for polling manager**

Create `somni-hud/tests/polling.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { Poller } from '../src/polling.ts'

describe('Poller', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('calls the fetch function on start', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const poller = new Poller(fn, 1000)
    poller.start()
    await vi.runOnlyPendingTimersAsync()
    expect(fn).toHaveBeenCalledTimes(1)
    poller.stop()
  })

  it('calls fetch function repeatedly at interval', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const poller = new Poller(fn, 1000)
    poller.start()
    await vi.advanceTimersByTimeAsync(3500)
    expect(fn.mock.calls.length).toBeGreaterThanOrEqual(3)
    poller.stop()
  })

  it('stops calling after stop()', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const poller = new Poller(fn, 1000)
    poller.start()
    await vi.advanceTimersByTimeAsync(1500)
    poller.stop()
    const count = fn.mock.calls.length
    await vi.advanceTimersByTimeAsync(3000)
    expect(fn.mock.calls.length).toBe(count)
  })

  it('backs off on failure', async () => {
    let callCount = 0
    const fn = vi.fn().mockImplementation(() => {
      callCount++
      if (callCount <= 3) return Promise.reject(new Error('fail'))
      return Promise.resolve(undefined)
    })
    const poller = new Poller(fn, 1000, [2000, 4000])
    poller.start()

    // First call (immediate) — fails, backoff to 2000
    await vi.advanceTimersByTimeAsync(100)
    expect(fn).toHaveBeenCalledTimes(1)

    // Wait 2000ms — second call — fails, backoff to 4000
    await vi.advanceTimersByTimeAsync(2000)
    expect(fn).toHaveBeenCalledTimes(2)

    // Wait 4000ms — third call — fails, stays at 4000 (max)
    await vi.advanceTimersByTimeAsync(4000)
    expect(fn).toHaveBeenCalledTimes(3)

    // Wait 4000ms — fourth call — succeeds, back to 1000
    await vi.advanceTimersByTimeAsync(4000)
    expect(fn).toHaveBeenCalledTimes(4)

    // Wait 1000ms — fifth call at normal interval
    await vi.advanceTimersByTimeAsync(1000)
    expect(fn).toHaveBeenCalledTimes(5)

    poller.stop()
  })

  it('trigger() fires immediately', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const poller = new Poller(fn, 60000) // very long interval
    poller.start()
    await vi.advanceTimersByTimeAsync(100)
    expect(fn).toHaveBeenCalledTimes(1)
    await poller.trigger()
    expect(fn).toHaveBeenCalledTimes(2)
    poller.stop()
  })

  it('setInterval changes the polling interval', async () => {
    const fn = vi.fn().mockResolvedValue(undefined)
    const poller = new Poller(fn, 5000)
    poller.start()
    await vi.advanceTimersByTimeAsync(100) // first call
    poller.setInterval(1000)
    await vi.advanceTimersByTimeAsync(3500)
    // At 1000ms interval, should have ~3 more calls
    expect(fn.mock.calls.length).toBeGreaterThanOrEqual(4)
    poller.stop()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npx vitest run tests/polling.test.ts
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement polling manager**

Create `somni-hud/src/polling.ts`:

```typescript
export class Poller {
  private fn: () => Promise<void>
  private intervalMs: number
  private backoffSteps: number[]
  private backoffIndex = 0
  private timer: ReturnType<typeof setTimeout> | null = null
  private running = false

  constructor(
    fn: () => Promise<void>,
    intervalMs: number,
    backoffSteps?: number[],
  ) {
    this.fn = fn
    this.intervalMs = intervalMs
    this.backoffSteps = backoffSteps ?? [
      intervalMs * 3,
      intervalMs * 6,
      intervalMs * 12,
    ]
  }

  start(): void {
    if (this.running) return
    this.running = true
    this.backoffIndex = 0
    this.schedule(0)
  }

  stop(): void {
    this.running = false
    if (this.timer !== null) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }

  async trigger(): Promise<void> {
    await this.execute()
  }

  setInterval(ms: number): void {
    this.intervalMs = ms
    if (this.running) {
      this.stop()
      this.running = true
      this.schedule(0)
    }
  }

  private schedule(delayMs: number): void {
    if (!this.running) return
    this.timer = setTimeout(() => {
      this.execute().then(() => {
        if (this.running) {
          const nextDelay = this.backoffIndex > 0
            ? this.backoffSteps[Math.min(this.backoffIndex - 1, this.backoffSteps.length - 1)]!
            : this.intervalMs
          this.schedule(nextDelay)
        }
      })
    }, delayMs)
  }

  private async execute(): Promise<void> {
    try {
      await this.fn()
      this.backoffIndex = 0
    } catch {
      this.backoffIndex++
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npx vitest run tests/polling.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/polling.ts tests/polling.test.ts
git commit -m "feat: add polling manager with exponential backoff"
```

---

## Task 6: Display Helpers

**Files:**
- Create: `somni-hud/src/display.ts`

- [ ] **Step 1: Create display helpers module**

This module wraps the verbose Even Hub SDK container APIs into simple helper functions. Since these call the SDK bridge directly (which requires a real WebView), they are tested via the simulator, not unit tests.

Create `somni-hud/src/display.ts`:

```typescript
import {
  TextContainerProperty,
  ListContainerProperty,
  ListItemContainerProperty,
  CreateStartUpPageContainer,
  RebuildPageContainer,
  TextContainerUpgrade,
  OsEventTypeList,
  type EvenAppBridge,
  type EvenHubEvent,
} from '@evenrealities/even_hub_sdk'

const DISPLAY_W = 576
const DISPLAY_H = 288

// ---------------------------------------------------------------------------
// Page lifecycle
// ---------------------------------------------------------------------------

export async function showTextPage(
  bridge: EvenAppBridge,
  content: string,
  containerId = 1,
  containerName = 'main',
): Promise<number> {
  const text = new TextContainerProperty({
    xPosition: 0,
    yPosition: 0,
    width: DISPLAY_W,
    height: DISPLAY_H,
    borderWidth: 0,
    borderColor: 5,
    paddingLength: 4,
    containerID: containerId,
    containerName: containerName,
    content: content.slice(0, 1000),
    isEventCapture: 1,
  })

  return bridge.createStartUpPageContainer(
    new CreateStartUpPageContainer({
      containerTotalNum: 1,
      textObject: [text],
    }),
  )
}

export async function updateText(
  bridge: EvenAppBridge,
  content: string,
  containerId = 1,
  containerName = 'main',
): Promise<boolean> {
  return bridge.textContainerUpgrade(
    new TextContainerUpgrade({
      containerID: containerId,
      containerName: containerName,
      content: content.slice(0, 2000),
    }),
  )
}

export async function showListPage(
  bridge: EvenAppBridge,
  items: string[],
  containerId = 1,
  containerName = 'list',
): Promise<number> {
  const list = new ListContainerProperty({
    xPosition: 0,
    yPosition: 0,
    width: DISPLAY_W,
    height: DISPLAY_H,
    borderWidth: 0,
    borderColor: 5,
    paddingLength: 4,
    containerID: containerId,
    containerName: containerName,
    isEventCapture: 1,
    itemContainer: new ListItemContainerProperty({
      itemCount: Math.min(items.length, 20),
      itemWidth: 0,
      isItemSelectBorderEn: 1,
      itemName: items.slice(0, 20),
    }),
  })

  return bridge.createStartUpPageContainer(
    new CreateStartUpPageContainer({
      containerTotalNum: 1,
      listObject: [list],
    }),
  )
}

export async function rebuildPage(
  bridge: EvenAppBridge,
  textContent: string,
  containerId = 1,
  containerName = 'main',
): Promise<boolean> {
  const text = new TextContainerProperty({
    xPosition: 0,
    yPosition: 0,
    width: DISPLAY_W,
    height: DISPLAY_H,
    borderWidth: 0,
    borderColor: 5,
    paddingLength: 4,
    containerID: containerId,
    containerName: containerName,
    content: textContent.slice(0, 1000),
    isEventCapture: 1,
  })

  return bridge.rebuildPageContainer(
    new RebuildPageContainer({
      containerTotalNum: 1,
      textObject: [text],
    }),
  )
}

// ---------------------------------------------------------------------------
// Event parsing helpers
// ---------------------------------------------------------------------------

export type InputAction = 'tap' | 'double-tap' | 'scroll-up' | 'scroll-down' | 'exit'

export function parseInputEvent(event: EvenHubEvent): InputAction | null {
  const sysType = event.sysEvent?.eventType ?? null
  const textType = event.textEvent?.eventType ?? null
  const listType = event.listEvent?.eventType ?? null

  // Double-tap from any source
  if (
    sysType === OsEventTypeList.DOUBLE_CLICK_EVENT ||
    textType === OsEventTypeList.DOUBLE_CLICK_EVENT ||
    listType === OsEventTypeList.DOUBLE_CLICK_EVENT
  ) {
    return 'double-tap'
  }

  // Tap — CLICK_EVENT is 0, arrives as undefined due to protobuf zero-omission
  if (
    sysType === OsEventTypeList.CLICK_EVENT ||
    sysType === undefined ||
    textType === OsEventTypeList.CLICK_EVENT ||
    textType === undefined ||
    listType === OsEventTypeList.CLICK_EVENT ||
    listType === undefined
  ) {
    // Only treat as tap if at least one event source is present
    if (event.sysEvent || event.textEvent || event.listEvent) {
      return 'tap'
    }
  }

  // Scroll
  if (
    textType === OsEventTypeList.SCROLL_TOP_EVENT ||
    listType === OsEventTypeList.SCROLL_TOP_EVENT
  ) {
    return 'scroll-up'
  }
  if (
    textType === OsEventTypeList.SCROLL_BOTTOM_EVENT ||
    listType === OsEventTypeList.SCROLL_BOTTOM_EVENT
  ) {
    return 'scroll-down'
  }

  // System exit
  if (
    sysType === OsEventTypeList.SYSTEM_EXIT_EVENT ||
    sysType === OsEventTypeList.ABNORMAL_EXIT_EVENT
  ) {
    return 'exit'
  }

  return null
}

// ---------------------------------------------------------------------------
// Text formatting helpers
// ---------------------------------------------------------------------------

export function progressBar(fraction: number, width = 10): string {
  const filled = Math.round(fraction * width)
  const empty = width - filled
  return '█'.repeat(filled) + '░'.repeat(empty)
}

export function timeRemaining(seconds: number): string {
  if (seconds <= 0) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h${m.toString().padStart(2, '0')}m`
  return `${m}m`
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen - 1) + '…'
}
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/display.ts
git commit -m "feat: add display helpers for text pages, lists, events, formatting"
```

---

## Task 7: Home Assistant API Client

**Files:**
- Create: `somni-hud/src/api/ha.ts`
- Create: `somni-hud/tests/api/ha.test.ts`

- [ ] **Step 1: Write failing tests**

Create `somni-hud/tests/api/ha.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HaClient } from '../../src/api/ha.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('HaClient', () => {
  let client: HaClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new HaClient('http://ha.local', 'test-token')
  })

  describe('getEntities', () => {
    it('fetches states for given entity IDs', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([
          { entity_id: 'light.desk', state: 'on', attributes: { friendly_name: 'Desk Light' } },
          { entity_id: 'climate.living', state: '72', attributes: { friendly_name: 'Living Room', unit_of_measurement: '°F' } },
        ]),
      })

      const entities = await client.getEntities(['light.desk', 'climate.living'])
      expect(entities).toHaveLength(2)
      expect(entities[0]!.entity_id).toBe('light.desk')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://ha.local/api/states',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        }),
      )
    })

    it('returns empty array on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('network'))
      const entities = await client.getEntities(['light.desk'])
      expect(entities).toEqual([])
    })
  })

  describe('toggleEntity', () => {
    it('calls the correct service for a light', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      await client.toggleEntity('light.desk')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://ha.local/api/services/light/toggle',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ entity_id: 'light.desk' }),
        }),
      )
    })

    it('calls the correct service for a switch', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      await client.toggleEntity('switch.fan')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://ha.local/api/services/switch/toggle',
        expect.objectContaining({ method: 'POST' }),
      )
    })

    it('calls the correct service for a lock', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      await client.toggleEntity('lock.front_door')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://ha.local/api/services/lock/toggle',
        expect.objectContaining({ method: 'POST' }),
      )
    })
  })

  describe('getStatusSummary', () => {
    it('formats summary from entities', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([
          { entity_id: 'light.one', state: 'on', attributes: {} },
          { entity_id: 'light.two', state: 'on', attributes: {} },
          { entity_id: 'light.three', state: 'off', attributes: {} },
          { entity_id: 'climate.main', state: '72', attributes: { unit_of_measurement: '°F' } },
        ]),
      })

      client = new HaClient('http://ha.local', 'tok', ['light.one', 'light.two', 'light.three', 'climate.main'])
      const summary = await client.getStatusSummary()
      expect(summary).toContain('2 on')
    })
  })

  describe('isHealthy', () => {
    it('returns true when HA responds', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      expect(await client.isHealthy()).toBe(true)
    })

    it('returns false when HA is down', async () => {
      mockFetch.mockRejectedValue(new Error('down'))
      expect(await client.isHealthy()).toBe(false)
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npx vitest run tests/api/ha.test.ts
```

Expected: FAIL.

- [ ] **Step 3: Implement HA client**

Create `somni-hud/src/api/ha.ts`:

```typescript
import type { HaEntity, SectionStatus } from '../types.ts'

const TIMEOUT_MS = 5000

export class HaClient {
  private url: string
  private token: string
  private entityIds: string[]
  private cachedEntities: HaEntity[] = []
  lastUpdated = 0

  constructor(url: string, token: string, entityIds: string[] = []) {
    this.url = url.replace(/\/$/, '')
    this.token = token
    this.entityIds = entityIds
  }

  private async apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`,
          ...options.headers,
        },
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`HA HTTP ${response.status}`)
      return (await response.json()) as T
    } finally {
      clearTimeout(timeout)
    }
  }

  async getEntities(entityIds?: string[]): Promise<HaEntity[]> {
    const ids = entityIds ?? this.entityIds
    try {
      const allStates = await this.apiFetch<HaEntity[]>('/api/states')
      const filtered = allStates.filter((e) => ids.includes(e.entity_id))
      this.cachedEntities = filtered
      this.lastUpdated = Date.now()
      return filtered
    } catch {
      return []
    }
  }

  async toggleEntity(entityId: string): Promise<void> {
    const domain = entityId.split('.')[0]!
    await this.apiFetch(`/api/services/${domain}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ entity_id: entityId }),
    })
  }

  async getStatusSummary(): Promise<string> {
    const entities = await this.getEntities()
    if (entities.length === 0) return 'offline'

    const lightsOn = entities.filter(
      (e) => e.entity_id.startsWith('light.') && e.state === 'on',
    ).length
    const climate = entities.find((e) => e.entity_id.startsWith('climate.'))
    const temp = climate ? `${climate.state}${climate.attributes.unit_of_measurement ?? ''}` : ''

    const parts: string[] = []
    if (lightsOn > 0) parts.push(`${lightsOn} on`)
    if (temp) parts.push(temp)
    return parts.join('  ') || 'ok'
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.apiFetch('/api/')
      return true
    } catch {
      return false
    }
  }

  getCached(): HaEntity[] {
    return this.cachedEntities
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npx vitest run tests/api/ha.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/ha.ts tests/api/ha.test.ts
git commit -m "feat: add Home Assistant API client with entity fetch, toggle, status"
```

---

## Task 8: Moonraker API Client

**Files:**
- Create: `somni-hud/src/api/moonraker.ts`
- Create: `somni-hud/tests/api/moonraker.test.ts`

- [ ] **Step 1: Write failing tests**

Create `somni-hud/tests/api/moonraker.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MoonrakerClient } from '../../src/api/moonraker.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('MoonrakerClient', () => {
  let client: MoonrakerClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new MoonrakerClient('http://printer.local:7125')
  })

  describe('getPrinterData', () => {
    it('parses printer status from Moonraker response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: {
            status: {
              print_stats: {
                state: 'printing',
                filename: 'top_tray_v3.gcode',
                total_duration: 7200,
                print_duration: 4800,
              },
              heater_bed: { temperature: 60.1, target: 65.0 },
              extruder: { temperature: 215.3, target: 220.0 },
              display_status: { progress: 0.67 },
            },
          },
        }),
      })

      const data = await client.getPrinterData()
      expect(data.state).toBe('printing')
      expect(data.filename).toBe('top_tray_v3.gcode')
      expect(data.progress).toBeCloseTo(0.67)
      expect(data.hotendTemp).toBeCloseTo(215.3)
      expect(data.bedTemp).toBeCloseTo(60.1)
    })

    it('returns offline state on failure', async () => {
      mockFetch.mockRejectedValue(new Error('network'))
      const data = await client.getPrinterData()
      expect(data.state).toBe('offline')
    })
  })

  describe('pause/resume', () => {
    it('sends pause command', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      await client.pause()
      expect(mockFetch).toHaveBeenCalledWith(
        'http://printer.local:7125/printer/print/pause',
        expect.objectContaining({ method: 'POST' }),
      )
    })

    it('sends resume command', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      await client.resume()
      expect(mockFetch).toHaveBeenCalledWith(
        'http://printer.local:7125/printer/print/resume',
        expect.objectContaining({ method: 'POST' }),
      )
    })
  })

  describe('getStatusSummary', () => {
    it('formats summary for printing state', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: {
            status: {
              print_stats: { state: 'printing', filename: 'test.gcode', total_duration: 7200, print_duration: 4800 },
              heater_bed: { temperature: 60, target: 65 },
              extruder: { temperature: 215, target: 220 },
              display_status: { progress: 0.67 },
            },
          },
        }),
      })
      const summary = await client.getStatusSummary()
      expect(summary).toContain('67%')
    })

    it('formats summary for idle state', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          result: {
            status: {
              print_stats: { state: 'standby', filename: '', total_duration: 0, print_duration: 0 },
              heater_bed: { temperature: 25, target: 0 },
              extruder: { temperature: 25, target: 0 },
              display_status: { progress: 0 },
            },
          },
        }),
      })
      const summary = await client.getStatusSummary()
      expect(summary).toBe('idle')
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npx vitest run tests/api/moonraker.test.ts
```

Expected: FAIL.

- [ ] **Step 3: Implement Moonraker client**

Create `somni-hud/src/api/moonraker.ts`:

```typescript
import type { PrinterData } from '../types.ts'

const TIMEOUT_MS = 5000
const QUERY_OBJECTS = 'print_stats&heater_bed&extruder&display_status'

export class MoonrakerClient {
  private url: string
  private cachedData: PrinterData | null = null
  lastUpdated = 0

  constructor(url: string) {
    this.url = url.replace(/\/$/, '')
  }

  private async apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}${path}`, {
        ...options,
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`Moonraker HTTP ${response.status}`)
      return (await response.json()) as T
    } finally {
      clearTimeout(timeout)
    }
  }

  async getPrinterData(): Promise<PrinterData> {
    try {
      const resp = await this.apiFetch<{
        result: {
          status: {
            print_stats: { state: string; filename: string; total_duration: number; print_duration: number }
            heater_bed: { temperature: number; target: number }
            extruder: { temperature: number; target: number }
            display_status: { progress: number }
          }
        }
      }>(`/printer/objects/query?${QUERY_OBJECTS}`)

      const s = resp.result.status
      const ps = s.print_stats
      const progress = s.display_status.progress
      const elapsed = ps.print_duration
      const timeRemaining = progress > 0 ? (elapsed / progress) - elapsed : 0

      const state = this.mapState(ps.state)
      const data: PrinterData = {
        state,
        filename: ps.filename || '',
        progress,
        timeRemaining: Math.max(0, Math.round(timeRemaining)),
        hotendTemp: s.extruder.temperature,
        hotendTarget: s.extruder.target,
        bedTemp: s.heater_bed.temperature,
        bedTarget: s.heater_bed.target,
      }
      this.cachedData = data
      this.lastUpdated = Date.now()
      return data
    } catch {
      return this.cachedData ?? {
        state: 'offline',
        filename: '',
        progress: 0,
        timeRemaining: 0,
        hotendTemp: 0,
        hotendTarget: 0,
        bedTemp: 0,
        bedTarget: 0,
      }
    }
  }

  private mapState(raw: string): PrinterData['state'] {
    switch (raw) {
      case 'printing': return 'printing'
      case 'paused': return 'paused'
      case 'error': return 'error'
      case 'standby':
      case 'complete':
      case 'cancelled':
        return 'idle'
      default: return 'idle'
    }
  }

  async pause(): Promise<void> {
    await this.apiFetch('/printer/print/pause', { method: 'POST' })
  }

  async resume(): Promise<void> {
    await this.apiFetch('/printer/print/resume', { method: 'POST' })
  }

  async getStatusSummary(): Promise<string> {
    const data = await this.getPrinterData()
    if (data.state === 'offline') return 'offline'
    if (data.state === 'idle') return 'idle'
    if (data.state === 'paused') return 'paused'
    if (data.state === 'error') return 'error'
    const pct = Math.round(data.progress * 100)
    const h = Math.floor(data.timeRemaining / 3600)
    const m = Math.floor((data.timeRemaining % 3600) / 60)
    const time = h > 0 ? `${h}h${m.toString().padStart(2, '0')}m` : `${m}m`
    return `${pct}% ${time}`
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.apiFetch('/printer/info')
      return true
    } catch {
      return false
    }
  }

  getCached(): PrinterData | null {
    return this.cachedData
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npx vitest run tests/api/moonraker.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/moonraker.ts tests/api/moonraker.test.ts
git commit -m "feat: add Moonraker API client with printer status, pause/resume"
```

---

## Task 9: Even-Terminal API Client

**Files:**
- Create: `somni-hud/src/api/even-terminal.ts`
- Create: `somni-hud/tests/api/even-terminal.test.ts`

- [ ] **Step 1: Write failing tests**

Create `somni-hud/tests/api/even-terminal.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { EvenTerminalClient } from '../../src/api/even-terminal.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('EvenTerminalClient', () => {
  let client: EvenTerminalClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new EvenTerminalClient('http://et.local:3456', 'test-token')
  })

  describe('listSessions', () => {
    it('fetches sessions from the API', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([{ id: 's1', provider: 'claude' }]),
      })
      const sessions = await client.listSessions()
      expect(sessions).toHaveLength(1)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://et.local:3456/api/sessions?provider=claude',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        }),
      )
    })
  })

  describe('createConversation', () => {
    it('posts to create a new conversation', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 'conv1' }),
      })
      const result = await client.createConversation()
      expect(result).toEqual({ id: 'conv1' })
      expect(mockFetch).toHaveBeenCalledWith(
        'http://et.local:3456/api/conversations',
        expect.objectContaining({ method: 'POST' }),
      )
    })
  })

  describe('sendMessage', () => {
    it('posts message to the API', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 'msg1', content: 'response' }),
      })
      const result = await client.sendMessage('hello')
      expect(result).toEqual({ id: 'msg1', content: 'response' })
      expect(mockFetch).toHaveBeenCalledWith(
        'http://et.local:3456/api/messages',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ content: 'hello' }),
        }),
      )
    })
  })

  describe('getStatusSummary', () => {
    it('returns "idle" when no sessions', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })
      expect(await client.getStatusSummary()).toBe('idle')
    })

    it('returns "active" when sessions exist', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([{ id: 's1' }]),
      })
      expect(await client.getStatusSummary()).toBe('active')
    })

    it('returns "offline" on error', async () => {
      mockFetch.mockRejectedValue(new Error('down'))
      expect(await client.getStatusSummary()).toBe('offline')
    })
  })

  describe('isHealthy', () => {
    it('returns true when API responds', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })
      expect(await client.isHealthy()).toBe(true)
    })

    it('returns false when API is down', async () => {
      mockFetch.mockRejectedValue(new Error('down'))
      expect(await client.isHealthy()).toBe(false)
    })
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
npx vitest run tests/api/even-terminal.test.ts
```

Expected: FAIL.

- [ ] **Step 3: Implement even-terminal client**

Create `somni-hud/src/api/even-terminal.ts`:

```typescript
import type { Message } from '../types.ts'

const TIMEOUT_MS = 5000

export class EvenTerminalClient {
  private url: string
  private token: string
  private history: Message[] = []
  lastUpdated = 0

  constructor(url: string, token: string) {
    this.url = url.replace(/\/$/, '')
    this.token = token
  }

  private async apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`,
          ...options.headers,
        },
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`even-terminal HTTP ${response.status}`)
      return (await response.json()) as T
    } finally {
      clearTimeout(timeout)
    }
  }

  async listSessions(): Promise<Array<{ id: string; [key: string]: unknown }>> {
    return this.apiFetch('/api/sessions?provider=claude')
  }

  async createConversation(): Promise<{ id: string }> {
    return this.apiFetch('/api/conversations', { method: 'POST' })
  }

  async sendMessage(content: string): Promise<{ id: string; content: string }> {
    this.history.push({ role: 'user', content, timestamp: Date.now() })
    const result = await this.apiFetch<{ id: string; content: string }>('/api/messages', {
      method: 'POST',
      body: JSON.stringify({ content }),
    })
    this.history.push({ role: 'assistant', content: result.content, timestamp: Date.now() })
    this.lastUpdated = Date.now()
    return result
  }

  getHistory(): Message[] {
    return this.history
  }

  clearHistory(): void {
    this.history = []
  }

  async getStatusSummary(): Promise<string> {
    try {
      const sessions = await this.listSessions()
      return sessions.length > 0 ? 'active' : 'idle'
    } catch {
      return 'offline'
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.listSessions()
      return true
    } catch {
      return false
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npx vitest run tests/api/even-terminal.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/api/even-terminal.ts tests/api/even-terminal.test.ts
git commit -m "feat: add even-terminal API client for Claude Code sessions"
```

---

## Task 10: Hermes & OpenClaw API Clients

**Files:**
- Create: `somni-hud/src/api/hermes.ts`
- Create: `somni-hud/src/api/openclaw.ts`
- Create: `somni-hud/tests/api/hermes.test.ts`
- Create: `somni-hud/tests/api/openclaw.test.ts`

Both use the OpenAI-compatible `/v1/chat/completions` endpoint. The clients are near-identical, differing only in constructor config and model name.

- [ ] **Step 1: Write failing tests for Hermes**

Create `somni-hud/tests/api/hermes.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HermesClient } from '../../src/api/hermes.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('HermesClient', () => {
  let client: HermesClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new HermesClient('http://hermes.local:8642', 'hermes-key')
  })

  describe('chat', () => {
    it('sends a message via /v1/chat/completions', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          choices: [{ message: { role: 'assistant', content: 'Hello from Hermes' } }],
        }),
      })
      const reply = await client.chat('hi')
      expect(reply).toBe('Hello from Hermes')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://hermes.local:8642/v1/chat/completions',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer hermes-key',
          }),
        }),
      )
    })

    it('throws on empty response', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ choices: [{ message: { content: '' } }] }),
      })
      await expect(client.chat('hi')).rejects.toThrow('Empty response')
    })
  })

  describe('getStatusSummary', () => {
    it('returns "online" when healthy', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      expect(await client.getStatusSummary()).toBe('online')
    })

    it('returns "offline" when down', async () => {
      mockFetch.mockRejectedValue(new Error('down'))
      expect(await client.getStatusSummary()).toBe('offline')
    })
  })

  describe('history', () => {
    it('tracks conversation history', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          choices: [{ message: { role: 'assistant', content: 'reply' } }],
        }),
      })
      await client.chat('question')
      const history = client.getHistory()
      expect(history).toHaveLength(2)
      expect(history[0]!.role).toBe('user')
      expect(history[1]!.role).toBe('assistant')
    })
  })
})
```

- [ ] **Step 2: Write failing tests for OpenClaw**

Create `somni-hud/tests/api/openclaw.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { OpenClawClient } from '../../src/api/openclaw.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('OpenClawClient', () => {
  let client: OpenClawClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new OpenClawClient('http://openclaw.local:18789', 'oc-key')
  })

  describe('chat', () => {
    it('sends a message via /v1/chat/completions', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          choices: [{ message: { role: 'assistant', content: 'Hello from OpenClaw' } }],
        }),
      })
      const reply = await client.chat('hi')
      expect(reply).toBe('Hello from OpenClaw')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://openclaw.local:18789/v1/chat/completions',
        expect.objectContaining({ method: 'POST' }),
      )
    })
  })

  describe('getStatusSummary', () => {
    it('returns "online" when healthy', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
      expect(await client.getStatusSummary()).toBe('online')
    })
  })
})
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
npx vitest run tests/api/hermes.test.ts tests/api/openclaw.test.ts
```

Expected: FAIL.

- [ ] **Step 4: Implement Hermes client**

Create `somni-hud/src/api/hermes.ts`:

```typescript
import type { Message } from '../types.ts'

const TIMEOUT_MS = 60_000

interface ChatCompletionResponse {
  choices: Array<{ message: { role: string; content: string } }>
}

export class HermesClient {
  private url: string
  private token: string
  private history: Message[] = []
  lastUpdated = 0

  constructor(url: string, token: string) {
    this.url = url.replace(/\/$/, '')
    this.token = token
  }

  async chat(prompt: string): Promise<string> {
    this.history.push({ role: 'user', content: prompt, timestamp: Date.now() })

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify({
          messages: [{ role: 'user', content: prompt }],
          stream: false,
        }),
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`Hermes HTTP ${response.status}`)
      const data = (await response.json()) as ChatCompletionResponse
      const content = data.choices?.[0]?.message?.content
      if (!content) throw new Error('Empty response from Hermes')
      this.history.push({ role: 'assistant', content, timestamp: Date.now() })
      this.lastUpdated = Date.now()
      return content
    } finally {
      clearTimeout(timeout)
    }
  }

  getHistory(): Message[] {
    return this.history
  }

  clearHistory(): void {
    this.history = []
  }

  async getStatusSummary(): Promise<string> {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      try {
        const resp = await fetch(`${this.url}/health`, { signal: controller.signal })
        return resp.ok ? 'online' : 'offline'
      } finally {
        clearTimeout(timeout)
      }
    } catch {
      return 'offline'
    }
  }

  async isHealthy(): Promise<boolean> {
    return (await this.getStatusSummary()) === 'online'
  }
}
```

- [ ] **Step 5: Implement OpenClaw client**

Create `somni-hud/src/api/openclaw.ts`:

```typescript
import type { Message } from '../types.ts'

const TIMEOUT_MS = 60_000

interface ChatCompletionResponse {
  choices: Array<{ message: { role: string; content: string } }>
}

export class OpenClawClient {
  private url: string
  private token: string
  private history: Message[] = []
  lastUpdated = 0

  constructor(url: string, token: string) {
    this.url = url.replace(/\/$/, '')
    this.token = token
  }

  async chat(prompt: string): Promise<string> {
    this.history.push({ role: 'user', content: prompt, timestamp: Date.now() })

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.token}`,
        },
        body: JSON.stringify({
          model: 'openclaw:main',
          messages: [{ role: 'user', content: prompt }],
          stream: false,
        }),
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`OpenClaw HTTP ${response.status}`)
      const data = (await response.json()) as ChatCompletionResponse
      const content = data.choices?.[0]?.message?.content
      if (!content) throw new Error('Empty response from OpenClaw')
      this.history.push({ role: 'assistant', content, timestamp: Date.now() })
      this.lastUpdated = Date.now()
      return content
    } finally {
      clearTimeout(timeout)
    }
  }

  getHistory(): Message[] {
    return this.history
  }

  clearHistory(): void {
    this.history = []
  }

  async getStatusSummary(): Promise<string> {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 5000)
      try {
        const resp = await fetch(`${this.url}/health`, { signal: controller.signal })
        return resp.ok ? 'online' : 'offline'
      } finally {
        clearTimeout(timeout)
      }
    } catch {
      return 'offline'
    }
  }

  async isHealthy(): Promise<boolean> {
    return (await this.getStatusSummary()) === 'online'
  }
}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
npx vitest run tests/api/hermes.test.ts tests/api/openclaw.test.ts
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/api/hermes.ts src/api/openclaw.ts tests/api/hermes.test.ts tests/api/openclaw.test.ts
git commit -m "feat: add Hermes and OpenClaw chat clients (OpenAI-compatible)"
```

---

## Task 11: Prometheus & ArgoCD API Clients

**Files:**
- Create: `somni-hud/src/api/prometheus.ts`
- Create: `somni-hud/src/api/argocd.ts`
- Create: `somni-hud/tests/api/prometheus.test.ts`
- Create: `somni-hud/tests/api/argocd.test.ts`

- [ ] **Step 1: Write failing tests for Prometheus**

Create `somni-hud/tests/api/prometheus.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { PrometheusClient } from '../../src/api/prometheus.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('PrometheusClient', () => {
  let client: PrometheusClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new PrometheusClient('http://prom.local:9090')
  })

  describe('query', () => {
    it('sends a PromQL instant query', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          data: { resultType: 'vector', result: [{ value: [1234567890, '5'] }] },
        }),
      })
      const result = await client.query('count(kube_node_info)')
      expect(result).toEqual([{ value: [1234567890, '5'] }])
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/query?query='),
        expect.any(Object),
      )
    })
  })

  describe('getScalar', () => {
    it('returns numeric value from single-result query', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          data: { resultType: 'vector', result: [{ value: [0, '42'] }] },
        }),
      })
      expect(await client.getScalar('count(up)')).toBe(42)
    })

    it('returns 0 when no results', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          status: 'success',
          data: { resultType: 'vector', result: [] },
        }),
      })
      expect(await client.getScalar('count(up)')).toBe(0)
    })

    it('returns 0 on error', async () => {
      mockFetch.mockRejectedValue(new Error('down'))
      expect(await client.getScalar('count(up)')).toBe(0)
    })
  })
})
```

- [ ] **Step 2: Write failing tests for ArgoCD**

Create `somni-hud/tests/api/argocd.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ArgoCdClient } from '../../src/api/argocd.ts'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('ArgoCdClient', () => {
  let client: ArgoCdClient

  beforeEach(() => {
    vi.clearAllMocks()
    client = new ArgoCdClient('http://argocd.local', 'argo-token')
  })

  describe('getApplications', () => {
    it('fetches and summarizes app sync status', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          items: [
            { metadata: { name: 'app1' }, status: { sync: { status: 'Synced' }, health: { status: 'Healthy' } } },
            { metadata: { name: 'app2' }, status: { sync: { status: 'Synced' }, health: { status: 'Healthy' } } },
            { metadata: { name: 'app3' }, status: { sync: { status: 'OutOfSync' }, health: { status: 'Degraded' } } },
          ],
        }),
      })
      const result = await client.getApplications()
      expect(result.total).toBe(3)
      expect(result.synced).toBe(2)
      expect(result.outOfSync).toEqual(['app3'])
    })
  })

  describe('getStatusSummary', () => {
    it('formats sync summary', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          items: [
            { metadata: { name: 'a' }, status: { sync: { status: 'Synced' }, health: { status: 'Healthy' } } },
            { metadata: { name: 'b' }, status: { sync: { status: 'Synced' }, health: { status: 'Healthy' } } },
          ],
        }),
      })
      expect(await client.getStatusSummary()).toBe('2/2 synced')
    })
  })
})
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
npx vitest run tests/api/prometheus.test.ts tests/api/argocd.test.ts
```

Expected: FAIL.

- [ ] **Step 4: Implement Prometheus client**

Create `somni-hud/src/api/prometheus.ts`:

```typescript
const TIMEOUT_MS = 5000

interface PromQueryResult {
  metric?: Record<string, string>
  value: [number, string]
}

interface PromResponse {
  status: string
  data: {
    resultType: string
    result: PromQueryResult[]
  }
}

export class PrometheusClient {
  private url: string
  lastUpdated = 0

  constructor(url: string) {
    this.url = url.replace(/\/$/, '')
  }

  async query(promql: string): Promise<PromQueryResult[]> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const encoded = encodeURIComponent(promql)
      const response = await fetch(`${this.url}/api/v1/query?query=${encoded}`, {
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`Prometheus HTTP ${response.status}`)
      const data = (await response.json()) as PromResponse
      this.lastUpdated = Date.now()
      return data.data.result
    } finally {
      clearTimeout(timeout)
    }
  }

  async getScalar(promql: string): Promise<number> {
    try {
      const results = await this.query(promql)
      if (results.length === 0) return 0
      return parseFloat(results[0]!.value[1]) || 0
    } catch {
      return 0
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
      try {
        const resp = await fetch(`${this.url}/-/healthy`, { signal: controller.signal })
        return resp.ok
      } finally {
        clearTimeout(timeout)
      }
    } catch {
      return false
    }
  }
}
```

- [ ] **Step 5: Implement ArgoCD client**

Create `somni-hud/src/api/argocd.ts`:

```typescript
const TIMEOUT_MS = 5000

interface ArgoApp {
  metadata: { name: string }
  status: {
    sync: { status: string }
    health: { status: string }
  }
}

interface ArgoAppList {
  items: ArgoApp[]
}

export interface ArgoSummary {
  total: number
  synced: number
  outOfSync: string[]
}

export class ArgoCdClient {
  private url: string
  private token: string
  private cached: ArgoSummary | null = null
  lastUpdated = 0

  constructor(url: string, token: string) {
    this.url = url.replace(/\/$/, '')
    this.token = token
  }

  async getApplications(): Promise<ArgoSummary> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
      const response = await fetch(`${this.url}/api/v1/applications`, {
        headers: {
          Authorization: `Bearer ${this.token}`,
        },
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`ArgoCD HTTP ${response.status}`)
      const data = (await response.json()) as ArgoAppList
      const apps = data.items ?? []
      const synced = apps.filter((a) => a.status.sync.status === 'Synced').length
      const outOfSync = apps
        .filter((a) => a.status.sync.status !== 'Synced')
        .map((a) => a.metadata.name)

      const summary: ArgoSummary = { total: apps.length, synced, outOfSync }
      this.cached = summary
      this.lastUpdated = Date.now()
      return summary
    } finally {
      clearTimeout(timeout)
    }
  }

  async getStatusSummary(): Promise<string> {
    try {
      const data = await this.getApplications()
      if (data.outOfSync.length > 0) {
        return `${data.synced}/${data.total} synced`
      }
      return `${data.total}/${data.total} synced`
    } catch {
      return 'offline'
    }
  }

  async isHealthy(): Promise<boolean> {
    try {
      await this.getApplications()
      return true
    } catch {
      return false
    }
  }

  getCached(): ArgoSummary | null {
    return this.cached
  }
}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
npx vitest run tests/api/prometheus.test.ts tests/api/argocd.test.ts
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/api/prometheus.ts src/api/argocd.ts tests/api/prometheus.test.ts tests/api/argocd.test.ts
git commit -m "feat: add Prometheus and ArgoCD API clients for cluster monitoring"
```

---

## Task 12: Grid Home Screen

**Files:**
- Create: `somni-hud/src/screens/grid.ts`

- [ ] **Step 1: Implement the grid home screen**

Create `somni-hud/src/screens/grid.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import { showTextPage, updateText } from '../display.ts'
import { SECTION_ORDER, SECTION_LABELS, type SectionStatus } from '../types.ts'

const HIGHLIGHT_MARKER = '> '
const NORMAL_MARKER = '  '

export function formatGrid(
  statuses: Map<number, SectionStatus>,
  highlight: number,
): string {
  const lines: string[] = []
  lines.push('--- Somni HUD ---')
  lines.push('')

  for (let i = 0; i < SECTION_ORDER.length; i++) {
    const section = SECTION_ORDER[i]!
    const label = SECTION_LABELS[section]
    const status = statuses.get(section)
    const marker = i === highlight ? HIGHLIGHT_MARKER : NORMAL_MARKER
    const summary = status?.summary ?? 'loading...'
    const health = status?.healthy === false ? ' !' : ''
    lines.push(`${marker}${label}${health}`)
    lines.push(`${NORMAL_MARKER}  ${summary}`)
  }

  return lines.join('\n')
}

export async function renderGrid(
  bridge: EvenAppBridge,
  statuses: Map<number, SectionStatus>,
  highlight: number,
  isFirstRender: boolean,
): Promise<void> {
  const content = formatGrid(statuses, highlight)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/screens/grid.ts
git commit -m "feat: add grid home screen with status badges and highlight"
```

---

## Task 13: Section Card Screens (Home, Printer, Cluster)

**Files:**
- Create: `somni-hud/src/screens/home.ts`
- Create: `somni-hud/src/screens/printer.ts`
- Create: `somni-hud/src/screens/cluster.ts`

- [ ] **Step 1: Implement Home (HA) screen**

Create `somni-hud/src/screens/home.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import type { HaEntity } from '../types.ts'
import { showListPage, showTextPage, updateText } from '../display.ts'
import type { HaClient } from '../api/ha.ts'

export function formatEntityList(entities: HaEntity[]): string[] {
  return entities.map((e) => {
    const name = e.attributes.friendly_name ?? e.entity_id
    const unit = e.attributes.unit_of_measurement ?? ''
    return `${name}: ${e.state}${unit}`
  })
}

export function formatEntityDetail(entities: HaEntity[], scrollOffset: number): string {
  const lines: string[] = ['--- Home ---', '']
  const visible = entities.slice(scrollOffset, scrollOffset + 8)
  for (const e of visible) {
    const name = e.attributes.friendly_name ?? e.entity_id
    const unit = e.attributes.unit_of_measurement ?? ''
    lines.push(`${name}: ${e.state}${unit}`)
  }
  if (entities.length > scrollOffset + 8) {
    lines.push('', `... ${entities.length - scrollOffset - 8} more`)
  }
  return lines.join('\n')
}

export async function renderHome(
  bridge: EvenAppBridge,
  haClient: HaClient,
  scrollOffset: number,
  isFirstRender: boolean,
): Promise<void> {
  const entities = await haClient.getEntities()
  const content = formatEntityDetail(entities.length > 0 ? entities : haClient.getCached(), scrollOffset)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}
```

- [ ] **Step 2: Implement Printer screen**

Create `somni-hud/src/screens/printer.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import type { PrinterData } from '../types.ts'
import { showTextPage, updateText, progressBar, timeRemaining, truncate } from '../display.ts'
import type { MoonrakerClient } from '../api/moonraker.ts'

export function formatPrinter(data: PrinterData): string {
  const lines: string[] = ['--- Printer ---', '']

  if (data.state === 'offline') {
    lines.push('Printer offline')
    return lines.join('\n')
  }

  if (data.state === 'idle') {
    lines.push('Printer idle')
    lines.push('')
    lines.push(`Hotend: ${Math.round(data.hotendTemp)}C`)
    lines.push(`Bed:    ${Math.round(data.bedTemp)}C`)
    return lines.join('\n')
  }

  lines.push(`File: ${truncate(data.filename, 40)}`)
  lines.push(`${progressBar(data.progress)} ${Math.round(data.progress * 100)}%`)
  lines.push(`Time left: ${timeRemaining(data.timeRemaining)}`)
  lines.push('')
  lines.push(`Hotend: ${Math.round(data.hotendTemp)}/${Math.round(data.hotendTarget)}C`)
  lines.push(`Bed:    ${Math.round(data.bedTemp)}/${Math.round(data.bedTarget)}C`)
  lines.push('')
  lines.push(`State: ${data.state}`)

  if (data.state === 'printing') {
    lines.push('', 'Tap to pause')
  } else if (data.state === 'paused') {
    lines.push('', 'Tap to resume')
  }

  return lines.join('\n')
}

export async function renderPrinter(
  bridge: EvenAppBridge,
  moonrakerClient: MoonrakerClient,
  isFirstRender: boolean,
): Promise<void> {
  const data = await moonrakerClient.getPrinterData()
  const content = formatPrinter(data)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}
```

- [ ] **Step 3: Implement Cluster screen**

Create `somni-hud/src/screens/cluster.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import type { ClusterData } from '../types.ts'
import { showTextPage, updateText } from '../display.ts'
import type { PrometheusClient } from '../api/prometheus.ts'
import type { ArgoCdClient } from '../api/argocd.ts'

export async function fetchClusterData(
  prom: PrometheusClient,
  argo: ArgoCdClient,
): Promise<ClusterData> {
  const [nodeCount, podRunning, podPending, podFailed, alertsFiring, argoSummary] =
    await Promise.all([
      prom.getScalar('count(kube_node_info)'),
      prom.getScalar('count(kube_pod_status_phase{phase="Running"})'),
      prom.getScalar('count(kube_pod_status_phase{phase="Pending"})'),
      prom.getScalar('count(kube_pod_status_phase{phase="Failed"})'),
      prom.getScalar('count(ALERTS{alertstate="firing"})'),
      argo.getApplications().catch(() => ({ total: 0, synced: 0, outOfSync: [] as string[] })),
    ])

  return {
    nodeCount,
    nodesReady: nodeCount, // Prometheus query already filters for info, refine later
    podTotal: podRunning + podPending + podFailed,
    podRunning,
    podPending,
    podFailed,
    alertsFiring,
    argoTotal: argoSummary.total,
    argoSynced: argoSummary.synced,
    argoOutOfSync: argoSummary.outOfSync,
  }
}

export function formatCluster(data: ClusterData): string {
  const lines: string[] = ['--- Cluster ---', '']

  lines.push(`ArgoCD: ${data.argoSynced}/${data.argoTotal} synced`)
  if (data.argoOutOfSync.length > 0) {
    for (const app of data.argoOutOfSync.slice(0, 5)) {
      lines.push(`  ! ${app}`)
    }
    if (data.argoOutOfSync.length > 5) {
      lines.push(`  ... +${data.argoOutOfSync.length - 5} more`)
    }
  }

  lines.push('')
  lines.push(`Nodes: ${data.nodeCount}`)
  lines.push(`Pods: ${data.podRunning} running`)

  if (data.podPending > 0) lines.push(`  ${data.podPending} pending`)
  if (data.podFailed > 0) lines.push(`  ${data.podFailed} failed`)

  if (data.alertsFiring > 0) {
    lines.push('')
    lines.push(`Alerts: ${data.alertsFiring} firing`)
  }

  return lines.join('\n')
}

export async function renderCluster(
  bridge: EvenAppBridge,
  prom: PrometheusClient,
  argo: ArgoCdClient,
  isFirstRender: boolean,
): Promise<void> {
  const data = await fetchClusterData(prom, argo)
  const content = formatCluster(data)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}
```

- [ ] **Step 4: Verify all compile**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add src/screens/home.ts src/screens/printer.ts src/screens/cluster.ts
git commit -m "feat: add Home, Printer, and Cluster card screens"
```

---

## Task 14: Terminal & Agents Screens

**Files:**
- Create: `somni-hud/src/screens/terminal.ts`
- Create: `somni-hud/src/screens/agents.ts`

- [ ] **Step 1: Implement Terminal screen**

Create `somni-hud/src/screens/terminal.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import type { Message } from '../types.ts'
import { showTextPage, updateText, truncate } from '../display.ts'
import type { EvenTerminalClient } from '../api/even-terminal.ts'

const MAX_VISIBLE_CHARS = 1800

export function formatConversation(history: Message[]): string {
  if (history.length === 0) {
    return '--- Claude Code ---\n\nTap to speak\nDouble-tap to exit'
  }

  const lines: string[] = []
  for (const msg of history) {
    const prefix = msg.role === 'user' ? 'You' : 'Claude'
    lines.push(`${prefix}: ${msg.content}`)
    lines.push('')
  }

  let text = lines.join('\n')
  // Keep only the tail that fits the 2000-char upgrade limit
  if (text.length > MAX_VISIBLE_CHARS) {
    text = '...\n' + text.slice(text.length - MAX_VISIBLE_CHARS + 4)
  }
  return text
}

export async function renderTerminal(
  bridge: EvenAppBridge,
  client: EvenTerminalClient,
  isFirstRender: boolean,
): Promise<void> {
  const content = formatConversation(client.getHistory())
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}

export async function handleTerminalMessage(
  bridge: EvenAppBridge,
  client: EvenTerminalClient,
  text: string,
): Promise<void> {
  // Show user message immediately
  await updateText(bridge, formatConversation(client.getHistory()) + '\n\nYou: ' + text + '\n\n...')

  try {
    await client.sendMessage(text)
    await updateText(bridge, formatConversation(client.getHistory()))
  } catch {
    const history = client.getHistory()
    await updateText(bridge, formatConversation(history) + '\n\n[Error — tap to retry]')
  }
}
```

- [ ] **Step 2: Implement Agents screen**

Create `somni-hud/src/screens/agents.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import { AgentId, AGENT_LABELS, type AgentStatus, type Message } from '../types.ts'
import { showTextPage, showListPage, updateText } from '../display.ts'
import type { EvenTerminalClient } from '../api/even-terminal.ts'
import type { HermesClient } from '../api/hermes.ts'
import type { OpenClawClient } from '../api/openclaw.ts'

export interface AgentClients {
  claude: EvenTerminalClient
  hermes: HermesClient
  openclaw: OpenClawClient
}

export async function getAgentStatuses(clients: AgentClients): Promise<AgentStatus[]> {
  const [claudeHealthy, hermesHealthy, openclawHealthy] = await Promise.all([
    clients.claude.isHealthy(),
    clients.hermes.isHealthy(),
    clients.openclaw.isHealthy(),
  ])
  return [
    { id: AgentId.CLAUDE, label: AGENT_LABELS[AgentId.CLAUDE], online: claudeHealthy },
    { id: AgentId.HERMES, label: AGENT_LABELS[AgentId.HERMES], online: hermesHealthy },
    { id: AgentId.OPENCLAW, label: AGENT_LABELS[AgentId.OPENCLAW], online: openclawHealthy },
  ]
}

export function formatAgentPicker(statuses: AgentStatus[], highlight: number): string {
  const lines: string[] = ['--- Agents ---', '']
  for (let i = 0; i < statuses.length; i++) {
    const s = statuses[i]!
    const marker = i === highlight ? '> ' : '  '
    const badge = s.online ? 'online' : 'offline'
    lines.push(`${marker}${s.label}  [${badge}]`)
  }
  lines.push('', 'Tap to connect')
  lines.push('Double-tap to exit')
  return lines.join('\n')
}

export function formatAgentConversation(agentLabel: string, history: Message[]): string {
  if (history.length === 0) {
    return `--- ${agentLabel} ---\n\nTap to speak\nDouble-tap to go back`
  }

  const lines: string[] = []
  for (const msg of history) {
    const prefix = msg.role === 'user' ? 'You' : agentLabel
    lines.push(`${prefix}: ${msg.content}`)
    lines.push('')
  }

  let text = lines.join('\n')
  if (text.length > 1800) {
    text = '...\n' + text.slice(text.length - 1796)
  }
  return text
}

export async function renderAgentPicker(
  bridge: EvenAppBridge,
  clients: AgentClients,
  highlight: number,
  isFirstRender: boolean,
): Promise<void> {
  const statuses = await getAgentStatuses(clients)
  const content = formatAgentPicker(statuses, highlight)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}

export async function renderAgentConversation(
  bridge: EvenAppBridge,
  agentId: AgentId,
  clients: AgentClients,
  isFirstRender: boolean,
): Promise<void> {
  const label = AGENT_LABELS[agentId]
  let history: Message[]
  switch (agentId) {
    case AgentId.CLAUDE:
      history = clients.claude.getHistory()
      break
    case AgentId.HERMES:
      history = clients.hermes.getHistory()
      break
    case AgentId.OPENCLAW:
      history = clients.openclaw.getHistory()
      break
  }
  const content = formatAgentConversation(label, history)
  if (isFirstRender) {
    await showTextPage(bridge, content)
  } else {
    await updateText(bridge, content)
  }
}

export async function handleAgentMessage(
  bridge: EvenAppBridge,
  agentId: AgentId,
  clients: AgentClients,
  text: string,
): Promise<void> {
  const label = AGENT_LABELS[agentId]

  try {
    switch (agentId) {
      case AgentId.CLAUDE:
        await updateText(bridge, formatAgentConversation(label, clients.claude.getHistory()) + '\n\nYou: ' + text + '\n\n...')
        await clients.claude.sendMessage(text)
        break
      case AgentId.HERMES:
        // chat() internally pushes user + assistant to history
        await updateText(bridge, formatAgentConversation(label, clients.hermes.getHistory()) + '\n\nYou: ' + text + '\n\n...')
        await clients.hermes.chat(text)
        break
      case AgentId.OPENCLAW:
        // chat() internally pushes user + assistant to history
        await updateText(bridge, formatAgentConversation(label, clients.openclaw.getHistory()) + '\n\nYou: ' + text + '\n\n...')
        await clients.openclaw.chat(text)
        break
    }
  } catch {
    // Error already in display, keep current state
  }

  await renderAgentConversation(bridge, agentId, clients, false)
}
```

- [ ] **Step 3: Verify all compile**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add src/screens/terminal.ts src/screens/agents.ts
git commit -m "feat: add Terminal and Agents screens with conversational UI"
```

---

## Task 15: Setup Screen

**Files:**
- Create: `somni-hud/src/screens/setup.ts`

- [ ] **Step 1: Implement setup screen**

Create `somni-hud/src/screens/setup.ts`:

```typescript
import type { EvenAppBridge } from '@evenrealities/even_hub_sdk'
import { showTextPage, updateText } from '../display.ts'
import { saveConfig, DEFAULT_POLLING } from '../config.ts'
import type { SomniHudConfig } from '../types.ts'

/**
 * Setup is driven from the phone-side WebView companion UI.
 * The glasses display shows a simple "Setup in progress..." message.
 * The actual config form is rendered in the phone WebView DOM
 * (outside the SDK bridge), and config is saved via the SDK bridge
 * once complete.
 *
 * For v1, we provide a programmatic setup that accepts a config object
 * and saves it. The phone-side UI can be added as an enhancement.
 */

export async function renderSetupPrompt(bridge: EvenAppBridge): Promise<void> {
  const content = [
    '--- Somni HUD Setup ---',
    '',
    'Open the companion app',
    'on your phone to configure',
    'your service endpoints.',
    '',
    'After saving, the HUD will',
    'start automatically.',
  ].join('\n')

  await showTextPage(bridge, content)
}

export async function completeSetup(
  bridge: EvenAppBridge,
  config: Partial<SomniHudConfig>,
): Promise<SomniHudConfig> {
  const fullConfig: SomniHudConfig = {
    ha: {
      url: config.ha?.url ?? '',
      token: config.ha?.token ?? '',
      entities: config.ha?.entities ?? [],
    },
    moonraker: {
      url: config.moonraker?.url ?? '',
    },
    evenTerminal: {
      url: config.evenTerminal?.url ?? '',
      token: config.evenTerminal?.token ?? '',
    },
    hermes: {
      url: config.hermes?.url ?? '',
      token: config.hermes?.token ?? '',
    },
    openclaw: {
      url: config.openclaw?.url ?? '',
      token: config.openclaw?.token ?? '',
    },
    prometheus: {
      url: config.prometheus?.url ?? '',
    },
    argocd: {
      url: config.argocd?.url ?? '',
      token: config.argocd?.token ?? '',
    },
    polling: {
      ...DEFAULT_POLLING,
      ...config.polling,
    },
  }

  await saveConfig(bridge, fullConfig)
  return fullConfig
}
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/screens/setup.ts
git commit -m "feat: add setup screen with config initialization"
```

---

## Task 16: Main Application Orchestrator

**Files:**
- Modify: `somni-hud/src/main.ts`

- [ ] **Step 1: Implement the full main.ts orchestrator**

Replace `somni-hud/src/main.ts` with the full application:

```typescript
import { waitForEvenAppBridge, type EvenAppBridge, type EvenHubEvent } from '@evenrealities/even_hub_sdk'
import { NavMachine } from './nav.ts'
import { NavState, Section, type SomniHudConfig, type SectionStatus, AgentId } from './types.ts'
import { loadConfig } from './config.ts'
import { parseInputEvent } from './display.ts'
import { Poller } from './polling.ts'

// API clients
import { HaClient } from './api/ha.ts'
import { MoonrakerClient } from './api/moonraker.ts'
import { EvenTerminalClient } from './api/even-terminal.ts'
import { HermesClient } from './api/hermes.ts'
import { OpenClawClient } from './api/openclaw.ts'
import { PrometheusClient } from './api/prometheus.ts'
import { ArgoCdClient } from './api/argocd.ts'

// Screens
import { renderGrid } from './screens/grid.ts'
import { renderHome } from './screens/home.ts'
import { renderPrinter } from './screens/printer.ts'
import { renderCluster } from './screens/cluster.ts'
import { renderTerminal, handleTerminalMessage } from './screens/terminal.ts'
import { renderAgentPicker, renderAgentConversation, handleAgentMessage, type AgentClients } from './screens/agents.ts'
import { renderSetupPrompt } from './screens/setup.ts'

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

let bridge: EvenAppBridge
let nav: NavMachine
let config: SomniHudConfig

// Clients
let haClient: HaClient
let moonrakerClient: MoonrakerClient
let etClient: EvenTerminalClient
let hermesClient: HermesClient
let openclawClient: OpenClawClient
let promClient: PrometheusClient
let argoClient: ArgoCdClient

// Status cache for grid tiles
const sectionStatuses = new Map<number, SectionStatus>()

// Pollers
const pollers: Poller[] = []

// Agent screen state
let agentHighlight = 0
let activeAgent: AgentId | null = null

// Track first render per screen transition
let needsFirstRender = true

// Scroll offset for home screen
let homeScrollOffset = 0

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

function initClients(cfg: SomniHudConfig): void {
  haClient = new HaClient(cfg.ha.url, cfg.ha.token, cfg.ha.entities)
  moonrakerClient = new MoonrakerClient(cfg.moonraker.url)
  etClient = new EvenTerminalClient(cfg.evenTerminal.url, cfg.evenTerminal.token)
  hermesClient = new HermesClient(cfg.hermes.url, cfg.hermes.token)
  openclawClient = new OpenClawClient(cfg.openclaw.url, cfg.openclaw.token)
  promClient = new PrometheusClient(cfg.prometheus.url)
  argoClient = new ArgoCdClient(cfg.argocd.url, cfg.argocd.token)
}

function getAgentClients(): AgentClients {
  return { claude: etClient, hermes: hermesClient, openclaw: openclawClient }
}

// ---------------------------------------------------------------------------
// Polling setup
// ---------------------------------------------------------------------------

function startPolling(cfg: SomniHudConfig): void {
  stopPolling()

  const updateStatus = (section: Section, summary: string, healthy: boolean) => {
    sectionStatuses.set(section, { summary, healthy, lastUpdated: Date.now() })
    if (nav.state === NavState.GRID) {
      renderGrid(bridge, sectionStatuses, nav.gridHighlight, false).catch(console.error)
    }
  }

  pollers.push(
    new Poller(async () => {
      const summary = await haClient.getStatusSummary()
      updateStatus(Section.HOME, summary, summary !== 'offline')
    }, cfg.polling.ha),
  )

  pollers.push(
    new Poller(async () => {
      const summary = await moonrakerClient.getStatusSummary()
      updateStatus(Section.PRINTER, summary, summary !== 'offline')
    }, cfg.polling.printer),
  )

  pollers.push(
    new Poller(async () => {
      const argoSummary = await argoClient.getStatusSummary()
      const alerts = await promClient.getScalar('count(ALERTS{alertstate="firing"})')
      const summary = alerts > 0 ? `${argoSummary} ${alerts} alerts` : argoSummary
      updateStatus(Section.CLUSTER, summary, argoSummary !== 'offline')
    }, cfg.polling.cluster),
  )

  pollers.push(
    new Poller(async () => {
      const summary = await etClient.getStatusSummary()
      updateStatus(Section.TERMINAL, summary, summary !== 'offline')
    }, cfg.polling.agents),
  )

  pollers.push(
    new Poller(async () => {
      const clients = getAgentClients()
      const [c, h, o] = await Promise.all([
        clients.claude.isHealthy(),
        clients.hermes.isHealthy(),
        clients.openclaw.isHealthy(),
      ])
      const online = [c, h, o].filter(Boolean).length
      updateStatus(Section.AGENTS, `${online} online`, online > 0)
    }, cfg.polling.agents),
  )

  for (const p of pollers) p.start()
}

function stopPolling(): void {
  for (const p of pollers) p.stop()
  pollers.length = 0
}

// ---------------------------------------------------------------------------
// Screen rendering
// ---------------------------------------------------------------------------

async function renderCurrentScreen(): Promise<void> {
  const first = needsFirstRender
  needsFirstRender = false

  switch (nav.state) {
    case NavState.SETUP:
      await renderSetupPrompt(bridge)
      break

    case NavState.GRID:
      await renderGrid(bridge, sectionStatuses, nav.gridHighlight, first)
      break

    case NavState.CARD:
      switch (nav.activeSection) {
        case Section.HOME:
          await renderHome(bridge, haClient, homeScrollOffset, first)
          break
        case Section.PRINTER:
          await renderPrinter(bridge, moonrakerClient, first)
          break
        case Section.CLUSTER:
          await renderCluster(bridge, promClient, argoClient, first)
          break
        case Section.TERMINAL:
          await renderTerminal(bridge, etClient, first)
          break
        case Section.AGENTS:
          await renderAgentPicker(bridge, getAgentClients(), agentHighlight, first)
          break
      }
      break

    case NavState.AGENT:
      if (nav.activeSection === Section.TERMINAL) {
        await renderTerminal(bridge, etClient, first)
      } else if (activeAgent) {
        await renderAgentConversation(bridge, activeAgent, getAgentClients(), first)
      }
      break
  }
}

// ---------------------------------------------------------------------------
// Input handling
// ---------------------------------------------------------------------------

function handleInput(event: EvenHubEvent): void {
  const action = parseInputEvent(event)
  if (!action) return

  if (action === 'exit') {
    stopPolling()
    bridge.shutDownPageContainer(1)
    return
  }

  const prevState = nav.state
  const prevSection = nav.activeSection

  switch (action) {
    case 'tap':
      if (nav.state === NavState.GRID) {
        nav.tap()
        needsFirstRender = true
        homeScrollOffset = 0
      } else if (nav.state === NavState.CARD) {
        if (nav.activeSection === Section.TERMINAL) {
          nav.tap() // enters AGENT
          needsFirstRender = true
        } else if (nav.activeSection === Section.AGENTS) {
          // Select agent from picker
          const agents = [AgentId.CLAUDE, AgentId.HERMES, AgentId.OPENCLAW]
          activeAgent = agents[agentHighlight] ?? AgentId.CLAUDE
          nav.tap() // enters AGENT
          needsFirstRender = true
        } else if (nav.activeSection === Section.HOME) {
          // Toggle the highlighted entity
          const entities = haClient.getCached()
          if (entities.length > 0) {
            const entity = entities[homeScrollOffset]
            if (entity) {
              haClient.toggleEntity(entity.entity_id).catch(console.error)
            }
          }
        } else if (nav.activeSection === Section.PRINTER) {
          // Pause/resume
          const cached = moonrakerClient.getCached()
          if (cached?.state === 'printing') {
            moonrakerClient.pause().catch(console.error)
          } else if (cached?.state === 'paused') {
            moonrakerClient.resume().catch(console.error)
          }
        }
      }
      break

    case 'double-tap':
      if (nav.state === NavState.AGENT) {
        if (nav.activeSection === Section.AGENTS) {
          // Back to agent picker
          activeAgent = null
          nav.doubleTap()
        } else {
          // Back to CARD (for terminal)
          nav.doubleTap()
        }
        needsFirstRender = true
      } else if (nav.state === NavState.CARD) {
        nav.doubleTap()
        needsFirstRender = true
      }
      break

    case 'scroll-up':
      if (nav.state === NavState.GRID) {
        nav.scrollUp()
      } else if (nav.state === NavState.CARD && nav.activeSection === Section.HOME) {
        homeScrollOffset = Math.max(0, homeScrollOffset - 1)
      } else if (nav.state === NavState.CARD && nav.activeSection === Section.AGENTS) {
        agentHighlight = (agentHighlight - 1 + 3) % 3
      } else if (nav.state === NavState.CARD) {
        nav.swipeLeft()
        needsFirstRender = true
      }
      break

    case 'scroll-down':
      if (nav.state === NavState.GRID) {
        nav.scrollDown()
      } else if (nav.state === NavState.CARD && nav.activeSection === Section.HOME) {
        homeScrollOffset++
      } else if (nav.state === NavState.CARD && nav.activeSection === Section.AGENTS) {
        agentHighlight = (agentHighlight + 1) % 3
      } else if (nav.state === NavState.CARD) {
        nav.swipeRight()
        needsFirstRender = true
      }
      break
  }

  renderCurrentScreen().catch(console.error)
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function boot(): Promise<void> {
  bridge = await waitForEvenAppBridge()
  nav = new NavMachine()

  config = (await loadConfig(bridge))!

  if (!config) {
    nav.enterSetup()
    await renderCurrentScreen()
    // Setup completion will be triggered from the phone-side UI
    // For now, listen for config changes
    return
  }

  initClients(config)

  // Initial render — show grid with loading state
  for (const s of [Section.HOME, Section.PRINTER, Section.CLUSTER, Section.TERMINAL, Section.AGENTS]) {
    sectionStatuses.set(s, { summary: 'loading...', healthy: true, lastUpdated: Date.now() })
  }

  needsFirstRender = true
  await renderCurrentScreen()

  // Start polling
  startPolling(config)

  // Listen for input
  bridge.onEvenHubEvent((event) => {
    handleInput(event)
  })
}

boot().catch(console.error)
```

- [ ] **Step 2: Verify it compiles**

```bash
npx tsc --noEmit
```

Expected: no errors (may need to adjust import paths or minor type issues).

- [ ] **Step 3: Commit**

```bash
git add src/main.ts
git commit -m "feat: wire up main orchestrator with nav, polling, screens, input handling"
```

---

## Task 17: Full Test Suite Pass & Typecheck

**Files:**
- All existing test files and source files

- [ ] **Step 1: Run full test suite**

```bash
cd /home/curiosity/mounted_drives/obsidian/obsidian/Somni/SomniApps/somni-hud
npx vitest run
```

Expected: all tests pass. Fix any failures.

- [ ] **Step 2: Run full typecheck**

```bash
npx tsc --noEmit
```

Expected: no type errors. Fix any issues.

- [ ] **Step 3: Build production bundle**

```bash
npm run build
```

Expected: successful build in `dist/`. Verify `dist/index.html` exists.

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test and type issues for full suite pass"
```

---

## Task 18: Documentation & Final Commit

**Files:**
- Create: `somni-hud/CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

Create `somni-hud/CLAUDE.md`:

```markdown
# CLAUDE.md

## Project Overview

Somni HUD is an Even Hub plugin for Even Realities G2 smart glasses — a unified Somni Labs command center with home control (HA), printer monitoring (Moonraker), cluster health (Prometheus + ArgoCD), Claude Code terminal (even-terminal), and agent access (Hermes, OpenClaw).

## Commands

```bash
npm run dev          # Vite dev server (port 5173, host: true for LAN)
npm run build        # Production build to dist/
npm run test         # Run Vitest tests
npm run typecheck    # TypeScript strict check
npm run pack         # Package as .ehpk for Even Hub
```

### Testing on device

```bash
evenhub-simulator http://localhost:5173    # Desktop simulator
evenhub qr --url "http://<tailscale-ip>:5173"  # QR sideload to glasses
```

## Architecture

- **Vanilla TypeScript + Vite** — no framework, no state library
- **Even Hub SDK** (`@evenrealities/even_hub_sdk`) — bridge to G2 glasses
- **API clients** (`src/api/`) — one per backend, all use native `fetch()`
- **Screens** (`src/screens/`) — one file per HUD section
- **Navigation** (`src/nav.ts`) — state machine: GRID → CARD → AGENT
- **Polling** (`src/polling.ts`) — per-section polling with exponential backoff
- **Config** (`src/config.ts`) — endpoints/tokens stored in SDK local storage

## Display Constraints

- 576 x 288 px, 4-bit greyscale (16 shades of green)
- Max 1000 chars for initial page, 2000 chars for updates
- Max 4 image containers + 8 other containers per page
- CLICK_EVENT (0) arrives as undefined — always check with `?? 0`

## Backend Services (over Tailscale)

| Service | Client | Protocol |
|---|---|---|
| Home Assistant | `src/api/ha.ts` | REST (`/api/states`, `/api/services/`) |
| Moonraker | `src/api/moonraker.ts` | REST (`/printer/objects/query`) |
| even-terminal | `src/api/even-terminal.ts` | REST + WS (port 3456) |
| Hermes | `src/api/hermes.ts` | `/v1/chat/completions` |
| OpenClaw | `src/api/openclaw.ts` | `/v1/chat/completions` |
| Prometheus | `src/api/prometheus.ts` | `/api/v1/query` |
| ArgoCD | `src/api/argocd.ts` | `/api/v1/applications` |
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with project overview and architecture"
```

- [ ] **Step 3: Final status check**

```bash
npx vitest run && npx tsc --noEmit && npm run build
```

Expected: all tests pass, no type errors, successful build.
