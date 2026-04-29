// Browser Runtime Adapter using Playwright CDP
// Following SPEC.md Section 4.5

import { chromium, type Browser, type Page, type ConsoleMessage } from "playwright";
import type { ConsoleEntry, NetworkEntry, Runtime } from "../types/index.js";
import { logger } from "../lib/logger.js";

export class BrowserRuntime {
  private browser: Browser | null = null;
  private consoleBuffer: ConsoleEntry[] = [];
  private networkBuffer: NetworkEntry[] = [];

  async launch(): Promise<void> {
    logger.info("Launching browser with CDP debugging");
    this.browser = await chromium.launch({
      args: ["--remote-debugging-port=9222"],
    });
    logger.debug("Browser launched successfully");
  }

  // TODO: accept page parameter to attach to existing browser session
  async attach(url: string): Promise<void> {
    if (!this.browser) throw new Error("Browser not launched. Call launch() first.");
    
    logger.info(`Attaching to URL: ${url}`);
    const context = await this.browser.newContext();
    const page = await context.newPage();

    // Console listener
    page.on("console", (msg: ConsoleMessage) => {
      const entry: ConsoleEntry = {
        type: "console",
        runtime: "browser" as Runtime,
        level: msg.type() as ConsoleEntry["level"],
        timestamp: Date.now(),
        messages: msg.args().map((arg) => arg.toString()),
        source: `${msg.location().url}:${msg.location().lineNumber}`,
        context: { url: page.url() },
      };
      this.consoleBuffer.push(entry);
    });

    // Page error listener
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
      this.consoleBuffer.push(entry);
    });

    // Network response listener
    page.on("response", async (response) => {
      const req = response.request();
      
      // Calculate response time from request timing if available
      let responseTime = 0;
      try {
        // Use type assertion for timing() as it may not be in all TypeScript definitions
        const timing = (response as unknown as { timing(): { responseStart?: number; requestStart?: number } | null }).timing();
        if (timing?.responseStart && timing?.requestStart) {
          responseTime = timing.responseStart - timing.requestStart;
        }
      } catch {
        // timing() may not be available in all Playwright versions
      }
      
      const entry: NetworkEntry = {
        type: "network",
        runtime: "browser" as Runtime,
        id: req.url(),
        method: req.method(),
        url: response.url(),
        path: new URL(response.url()).pathname,
        domain: new URL(response.url()).hostname,
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
      this.networkBuffer.push(entry);
    });

    await page.goto(url);
    logger.debug(`Navigated to ${url}, buffers initialized`);
  }

  getConsoleEntries(): ConsoleEntry[] {
    return [...this.consoleBuffer];
  }

  getNetworkEntries(): NetworkEntry[] {
    return [...this.networkBuffer];
  }

  clearBuffers(): void {
    this.consoleBuffer = [];
    this.networkBuffer = [];
    logger.debug("Browser runtime buffers cleared");
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      logger.info("Browser closed");
    }
  }
}

// Singleton instance for the MCP server
export const browserRuntime = new BrowserRuntime();