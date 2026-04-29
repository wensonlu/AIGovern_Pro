import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { validateString } from "../lib/validator.js";
import type { BrowserAttachArgs, BrowserAttachResult } from "../types/index.js";
import { logger } from "../lib/logger.js";

export function createBrowserAttachTool(): Tool {
  return {
    name: "debug_browser_attach",
    description: "Attach browser runtime to a URL and return a sessionId for subsequent debug tools",
    inputSchema: {
      type: "object",
      properties: {
        url: {
          type: "string",
          description: "Target page URL to open and monitor",
        },
        cdpEndpoint: {
          type: "string",
          description: "Optional CDP endpoint to attach to an existing Chrome instance",
        },
      },
      required: ["url"],
    },
  };
}

export async function handleBrowserAttach(args: BrowserAttachArgs): Promise<BrowserAttachResult> {
  validateString(args.url, "url");
  if (args.cdpEndpoint !== undefined) {
    validateString(args.cdpEndpoint, "cdpEndpoint");
  }

  logger.info(`Browser attach requested: ${args.url}`);
  const result = await browserRuntime.attach(args.url, args.cdpEndpoint);
  return {
    sessionId: result.sessionId,
    attachedUrl: result.attachedUrl,
    cdpEndpoint: args.cdpEndpoint,
  };
}
