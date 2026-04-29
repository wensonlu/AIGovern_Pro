// debug_error_summary tool
// Following SPEC.md Section 4.4.3

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type {
  ErrorSummaryArgs,
  ErrorSummaryResult,
  ErrorEntry,
  ErrorSummary,
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

  return Array.from(errorMap.values()).sort((a, b) => b.count - a.count);
}

export function createErrorSummaryTool(): Tool {
  return {
    name: "debug_error_summary",
    description: "Summarize all errors (console errors and failed network requests) from browser or Python runtime",
    inputSchema: {
      type: "object",
      properties: {
        runtime: {
          type: "string",
          enum: ["browser", "python"],
          description: "Target runtime to get error summary from",
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

export async function handleErrorSummary(args: ErrorSummaryArgs): Promise<ErrorSummaryResult> {
  logger.info(`Error summary requested for runtime: ${args.runtime}`);

  validateRuntime(args.runtime);
  if (args.timeRange) validateTimeRange(args.timeRange);

  let consoleEntries: ConsoleEntry[];
  let networkEntries: NetworkEntry[];

  if (args.runtime === "browser") {
    consoleEntries = browserRuntime.getConsoleEntries();
    networkEntries = browserRuntime.getNetworkEntries();
  } else {
    [consoleEntries, networkEntries] = await Promise.all([
      pythonRuntime.getConsoleEntries(),
      pythonRuntime.getNetworkEntries(),
    ]);
  }

  // Filter by time range
  if (args.timeRange) {
    consoleEntries = filterByTimeRange(consoleEntries, args.timeRange);
    networkEntries = filterByTimeRange(networkEntries, args.timeRange);
  }

  // Get console errors (level = error)
  const errorEntries = consoleEntries.filter((e) => e.level === "error");
  const errorList = deduplicateErrors(errorEntries);

  // Get network failures (status >= 400)
  const networkFails = networkEntries
    .filter((e) => e.status >= 400)
    .map((e) => ({
      url: e.url,
      status: e.status,
      message: e.statusText || `HTTP ${e.status}`,
    }));

  const summary: ErrorSummary = {
    type: "error_summary",
    runtime: args.runtime,
    errorCount: errorList.length,
    errors: errorList,
    networkFailCount: networkFails.length,
    networkFails,
  };

  const hasErrors = errorList.length > 0;
  const hasNetworkFails = networkFails.length > 0;

  logger.debug(`Error summary: ${errorList.length} errors, ${networkFails.length} network failures`);

  return { summary, hasErrors, hasNetworkFails };
}