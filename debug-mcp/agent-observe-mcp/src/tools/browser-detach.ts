import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { validateString } from "../lib/validator.js";
import type { BrowserDetachArgs, BrowserDetachResult } from "../types/index.js";
import { logger } from "../lib/logger.js";

export function createBrowserDetachTool(): Tool {
  return {
    name: "debug_browser_detach",
    description: "Detach and cleanup a browser debug session by sessionId",
    inputSchema: {
      type: "object",
      properties: {
        sessionId: {
          type: "string",
          description: "Browser session id returned by debug_browser_attach",
        },
      },
      required: ["sessionId"],
    },
  };
}

export async function handleBrowserDetach(args: BrowserDetachArgs): Promise<BrowserDetachResult> {
  validateString(args.sessionId, "sessionId");
  logger.info(`Browser detach requested: ${args.sessionId}`);
  const detached = await browserRuntime.detach(args.sessionId);
  return {
    sessionId: args.sessionId,
    detached,
  };
}
