// debug_collect_all tool
// Following SPEC.md Section 4.4.7

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type {
  CollectAllArgs,
  CollectAllResult,
  ErrorEntry,
  ConsoleEntry,
  NetworkEntry,
} from "../types/index.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import { validateRuntime, validateTimeRange, filterByTimeRange } from "../lib/validator.js";

function deduplicateErrors(entries: ConsoleEntry[]): ErrorEntry[] {
  const errorMap = new Map<string, ErrorEntry>();

  for (const entry of entries) {
    const key = entry.messages.join("|");
    if (!errorMap.has(key)) {
      errorMap.set(key, {
        message: entry.messages.join("\n"),
        stack: entry.stack ?? "",
        count: 1,
        firstSeen: entry.timestamp,
        lastSeen: entry.timestamp,
      });
    } else {
      const existing = errorMap.get(key)!;
      existing.count++;
      existing.lastSeen = entry.timestamp;
    }
  }

  return Array.from(errorMap.values());
}

export function createCollectAllTool(): Tool {
  return {
    name: "debug_collect_all",
    description: "Collect all debugging data (console logs, network requests, and error summary) in one call",
    inputSchema: {
      type: "object",
      properties: {
        runtime: {
          type: "string",
          enum: ["browser", "python"],
          description: "Target runtime to collect all data from",
        },
        sessionId: {
          type: "string",
          description: "Browser session id from debug_browser_attach (only used when runtime=browser)",
        },
        timeRange: {
          type: "object",
          properties: {
            since: { type: "number", description: "Start time in Unix ms" },
            until: { type: "number", description: "End time in Unix ms" },
          },
        },
      },
      required: ["runtime"],
    },
  };
}

export async function handleCollectAll(args: CollectAllArgs): Promise<CollectAllResult> {
  logger.info(`Collect all requested for runtime: ${args.runtime}`);

  validateRuntime(args.runtime);
  if (args.timeRange) validateTimeRange(args.timeRange);

  let consoleEntries: ConsoleEntry[];
  let networkEntries: NetworkEntry[];

  if (args.runtime === "browser") {
    consoleEntries = await browserRuntime.getConsoleEntries(args.sessionId);
    networkEntries = await browserRuntime.getNetworkEntries(args.sessionId);
  } else {
    [consoleEntries, networkEntries] = await Promise.all([
      pythonRuntime.getConsoleEntries(),
      pythonRuntime.getNetworkEntries(),
    ]);
  }

  // Filter by time range if provided
  if (args.timeRange) {
    consoleEntries = filterByTimeRange(consoleEntries, args.timeRange);
    networkEntries = filterByTimeRange(networkEntries, args.timeRange);
  }

  // Get error entries
  const errorEntries = consoleEntries.filter((e) => e.level === "error");
  const deduplicatedErrors = deduplicateErrors(errorEntries);

  // Get network failures
  const networkFailEntries = networkEntries.filter((e) => e.status >= 400);

  // Build error summary
  const errorSummary = {
    type: "error_summary" as const,
    runtime: args.runtime,
    errorCount: deduplicatedErrors.length,
    errors: deduplicatedErrors,
    networkFailCount: networkFailEntries.length,
    networkFails: networkFailEntries.map((e) => ({
      url: e.url,
      status: e.status,
      message: e.statusText || `HTTP ${e.status}`,
    })),
  };

  const stats = {
    consoleTotal: consoleEntries.length,
    networkTotal: networkEntries.length,
    errorCount: deduplicatedErrors.length,
    networkFailCount: networkFailEntries.length,
  };

  logger.debug(
    `Collect all result: ${stats.consoleTotal} console, ${stats.networkTotal} network, ${stats.errorCount} errors, ${stats.networkFailCount} network fails`
  );

  return {
    console: consoleEntries,
    network: networkEntries,
    errorSummary,
    stats,
  };
}
