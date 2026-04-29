// debug_console_snapshot tool
// Following SPEC.md Section 4.4.1

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type {
  ConsoleSnapshotArgs,
  ConsoleSnapshotResult,
  ConsoleEntry,
} from "../types/index.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import {
  validateRuntime,
  validateConsoleLevel,
  validateTimeRange,
  filterByTimeRange,
} from "../lib/validator.js";

export function createConsoleSnapshotTool(): Tool {
  return {
    name: "debug_console_snapshot",
    description: "Capture console logs from browser or Python runtime with optional time range and level filtering",
    inputSchema: {
      type: "object",
      properties: {
        runtime: {
          type: "string",
          enum: ["browser", "python"],
          description: "Target runtime to capture console from",
        },
        timeRange: {
          type: "object",
          properties: {
            since: { type: "number", description: "Start time in Unix ms" },
            until: { type: "number", description: "End time in Unix ms" },
          },
        },
        level: {
          type: "string",
          enum: ["log", "error", "warn", "info", "debug"],
          description: "Filter by console level",
        },
      },
      required: ["runtime"],
    },
  };
}

export async function handleConsoleSnapshot(
  args: ConsoleSnapshotArgs
): Promise<ConsoleSnapshotResult> {
  logger.info(`Console snapshot requested for runtime: ${args.runtime}`);

  validateRuntime(args.runtime);
  if (args.level !== undefined) validateConsoleLevel(args.level);
  if (args.timeRange) validateTimeRange(args.timeRange);

  let entries: ConsoleEntry[];

  if (args.runtime === "browser") {
    entries = browserRuntime.getConsoleEntries();
  } else {
    entries = await pythonRuntime.getConsoleEntries();
  }

  // Filter by time range
  if (args.timeRange) {
    entries = filterByTimeRange(entries, args.timeRange);
  }

  // Filter by level
  if (args.level) {
    entries = entries.filter((e) => e.level === args.level);
  }

  // Sort by timestamp ascending
  entries = entries.sort((a, b) => a.timestamp - b.timestamp);

  const now = Date.now();
  const since = args.timeRange?.since ?? (now - 3600000); // Default: last hour
  const until = args.timeRange?.until ?? now;

  logger.debug(`Console snapshot: ${entries.length} entries returned`);

  return {
    entries,
    total: entries.length,
    timeRange: { since, until },
  };
}