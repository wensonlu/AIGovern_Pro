import { randomUUID } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { chromium, type Browser, type BrowserContext, type Page, type ConsoleMessage } from "playwright";
import type { ConsoleEntry, NetworkEntry, Runtime } from "../types/index.js";
import { logger } from "../lib/logger.js";

interface BrowserSession {
  id: string;
  page: Page;
  context: BrowserContext;
  consoleBuffer: ConsoleEntry[];
  networkBuffer: NetworkEntry[];
  attachedUrl: string;
  cdpEndpoint?: string;
  createdAt: number;
  lastAccessAt: number;
}

const SESSION_IDLE_TTL_MS = 30 * 60 * 1000;
const SESSION_SWEEP_INTERVAL_MS = 60 * 1000;
const SESSION_STORE_PATH = path.join(process.cwd(), ".agent-observe-sessions.json");

interface PersistedSession {
  sessionId: string;
  attachedUrl: string;
  cdpEndpoint?: string;
  updatedAt: number;
}

export class BrowserRuntime {
  private launchedBrowser: Browser | null = null;
  private cleanupTimer: NodeJS.Timeout | null = null;
  private sessions = new Map<string, BrowserSession>();
  private currentSessionId: string | null = null;
  private persistedSessions = new Map<string, PersistedSession>();

  constructor() {
    this.loadPersistedSessions();
    this.startCleanupLoop();
  }

  private loadPersistedSessions(): void {
    try {
      if (!fs.existsSync(SESSION_STORE_PATH)) return;
      const raw = fs.readFileSync(SESSION_STORE_PATH, "utf-8");
      const parsed = JSON.parse(raw) as PersistedSession[];
      for (const item of parsed) {
        this.persistedSessions.set(item.sessionId, item);
      }
    } catch (err) {
      logger.error(`Failed to load persisted browser sessions: ${String(err)}`);
    }
  }

  private savePersistedSessions(): void {
    try {
      const serialized = JSON.stringify(Array.from(this.persistedSessions.values()), null, 2);
      fs.writeFileSync(SESSION_STORE_PATH, serialized, "utf-8");
    } catch (err) {
      logger.error(`Failed to persist browser sessions: ${String(err)}`);
    }
  }

  private startCleanupLoop(): void {
    if (this.cleanupTimer) return;
    this.cleanupTimer = setInterval(() => {
      this.cleanupExpiredSessions().catch((err) => {
        logger.error(`Browser session cleanup failed: ${String(err)}`);
      });
    }, SESSION_SWEEP_INTERVAL_MS);
  }

  private async getOrLaunchBrowser(): Promise<Browser> {
    if (this.launchedBrowser && this.launchedBrowser.isConnected()) {
      return this.launchedBrowser;
    }
    logger.info("Launching managed browser for debug sessions");
    this.launchedBrowser = await chromium.launch({
      headless: true,
      args: ["--remote-debugging-port=9222"],
    });
    return this.launchedBrowser;
  }

  private resolveSession(sessionId?: string): BrowserSession {
    const resolvedId = sessionId ?? this.currentSessionId;
    if (!resolvedId) {
      throw new Error("No active browser session. Call debug_browser_attach first.");
    }
    const session = this.sessions.get(resolvedId);
    if (!session) {
      throw new Error(`Browser session not found: ${resolvedId}`);
    }
    session.lastAccessAt = Date.now();
    return session;
  }

  private async resolveOrReviveSession(sessionId?: string): Promise<BrowserSession> {
    try {
      return this.resolveSession(sessionId);
    } catch (err) {
      const resolvedId = sessionId ?? this.currentSessionId;
      if (!resolvedId) throw err;
      const persisted = this.persistedSessions.get(resolvedId);
      if (!persisted) throw err;
      logger.info(`Reviving persisted browser session: ${resolvedId}`);
      await this.attach(persisted.attachedUrl, persisted.cdpEndpoint, resolvedId);
      return this.resolveSession(resolvedId);
    }
  }

  private bindPageListeners(session: BrowserSession): void {
    const { page } = session;

    page.on("console", (msg: ConsoleMessage) => {
      const level = msg.type();
      const mappedLevel: ConsoleEntry["level"] = (
        level === "warning" ? "warn" : level
      ) as ConsoleEntry["level"];

      const entry: ConsoleEntry = {
        type: "console",
        runtime: "browser" as Runtime,
        level: mappedLevel,
        timestamp: Date.now(),
        messages: msg.args().map((arg) => arg.toString()),
        source: `${msg.location().url}:${msg.location().lineNumber}`,
        context: { url: page.url() },
      };
      session.consoleBuffer.push(entry);
      session.lastAccessAt = Date.now();
    });

    page.on("pageerror", (err: Error) => {
      const entry: ConsoleEntry = {
        type: "console",
        runtime: "browser" as Runtime,
        level: "error",
        timestamp: Date.now(),
        messages: [err.message],
        stack: err.stack,
        source: page.url(),
        context: { url: page.url() },
      };
      session.consoleBuffer.push(entry);
      session.lastAccessAt = Date.now();
    });

    page.on("response", async (response) => {
      const req = response.request();
      let responseTime = 0;
      try {
        const timing = (
          response as unknown as { timing(): { responseStart?: number; requestStart?: number } | null }
        ).timing();
        if (timing?.responseStart && timing?.requestStart) {
          responseTime = timing.responseStart - timing.requestStart;
        }
      } catch {
        // ignored
      }

      const responseUrl = response.url();
      const parsedUrl = new URL(responseUrl);
      const entry: NetworkEntry = {
        type: "network",
        runtime: "browser" as Runtime,
        id: `${responseUrl}#${Date.now()}`,
        method: req.method(),
        url: responseUrl,
        path: parsedUrl.pathname,
        domain: parsedUrl.hostname,
        status: response.status(),
        statusText: response.statusText(),
        responseTime,
        requestHeaders: req.headers(),
        requestBody: req.postDataBuffer()?.toString() ?? undefined,
        responseHeaders: response.headers(),
        responseBody: await response.text().catch(() => undefined),
        validated: false,
        validationResult: { 符合预期: false },
        timestamp: Date.now(),
      };
      session.networkBuffer.push(entry);
      session.lastAccessAt = Date.now();
    });
  }

  private async resolvePageForCdp(context: BrowserContext, targetUrl: string): Promise<Page> {
    const pages = context.pages();
    if (pages.length === 0) {
      const page = await context.newPage();
      await page.goto(targetUrl);
      return page;
    }

    const exactMatch = pages.find((p) => p.url() === targetUrl);
    if (exactMatch) return exactMatch;

    const hostPath = new URL(targetUrl);
    const relaxedMatch = pages.find((p) => {
      try {
        const u = new URL(p.url());
        return u.host === hostPath.host && u.pathname === hostPath.pathname;
      } catch {
        return false;
      }
    });
    if (relaxedMatch) return relaxedMatch;

    const firstPage = pages[0];
    await firstPage.goto(targetUrl);
    return firstPage;
  }

  async attach(
    url: string,
    cdpEndpoint?: string,
    preferredSessionId?: string
  ): Promise<{ sessionId: string; attachedUrl: string }> {
    const browser = cdpEndpoint
      ? await chromium.connectOverCDP(cdpEndpoint)
      : await this.getOrLaunchBrowser();
    const context = browser.contexts()[0] ?? (await browser.newContext());
    const page = cdpEndpoint
      ? await this.resolvePageForCdp(context, url)
      : await context.newPage();
    const sessionId = preferredSessionId ?? randomUUID();

    const session: BrowserSession = {
      id: sessionId,
      page,
      context,
      consoleBuffer: [],
      networkBuffer: [],
      attachedUrl: url,
      cdpEndpoint,
      createdAt: Date.now(),
      lastAccessAt: Date.now(),
    };

    this.bindPageListeners(session);
    if (!cdpEndpoint) {
      await page.goto(url);
    }

    this.sessions.set(sessionId, session);
    this.currentSessionId = sessionId;
    this.persistedSessions.set(sessionId, {
      sessionId,
      attachedUrl: url,
      cdpEndpoint,
      updatedAt: Date.now(),
    });
    this.savePersistedSessions();
    logger.info(`Browser session attached: ${sessionId} -> ${url}`);

    return { sessionId, attachedUrl: url };
  }

  async getConsoleEntries(sessionId?: string): Promise<ConsoleEntry[]> {
    return [...(await this.resolveOrReviveSession(sessionId)).consoleBuffer];
  }

  async getNetworkEntries(sessionId?: string): Promise<NetworkEntry[]> {
    return [...(await this.resolveOrReviveSession(sessionId)).networkBuffer];
  }

  clearBuffers(sessionId?: string): void {
    const session = this.resolveSession(sessionId);
    session.consoleBuffer = [];
    session.networkBuffer = [];
    logger.debug(`Browser runtime buffers cleared for session ${session.id}`);
  }

  async detach(sessionId: string): Promise<boolean> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }
    try {
      await session.page.close();
    } catch {
      // ignored
    }
    try {
      await session.context.close();
    } catch {
      // ignored
    }
    this.sessions.delete(sessionId);
    this.persistedSessions.delete(sessionId);
    this.savePersistedSessions();
    if (this.currentSessionId === sessionId) {
      this.currentSessionId = this.sessions.size > 0
        ? Array.from(this.sessions.keys())[this.sessions.size - 1]
        : null;
    }
    logger.info(`Browser session detached: ${sessionId}`);
    return true;
  }

  private async cleanupExpiredSessions(): Promise<void> {
    const now = Date.now();
    const expired: string[] = [];
    for (const [sessionId, session] of this.sessions.entries()) {
      if (now - session.lastAccessAt > SESSION_IDLE_TTL_MS) {
        expired.push(sessionId);
      }
    }
    for (const sessionId of expired) {
      await this.detach(sessionId);
      logger.info(`Browser session expired and detached: ${sessionId}`);
    }
  }

  async close(): Promise<void> {
    const sessionIds = Array.from(this.sessions.keys());
    for (const sessionId of sessionIds) {
      await this.detach(sessionId);
    }
    if (this.launchedBrowser) {
      await this.launchedBrowser.close();
      this.launchedBrowser = null;
      logger.info("Managed browser closed");
    }
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }
}

export const browserRuntime = new BrowserRuntime();
