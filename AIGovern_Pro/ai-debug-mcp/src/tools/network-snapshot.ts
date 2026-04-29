// debug_network_snapshot tool
// Following SPEC.md Section 4.4.2

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type {
  NetworkSnapshotArgs,
  NetworkSnapshotResult,
  NetworkEntry,
} from "../types/index.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import {
  validateRuntime,
  validateTimeRange,
  filterByTimeRange,
  matchUrlPattern,
} from "../lib/validator.js";

export function createNetworkSnapshotTool(): Tool {
  return {
    name: "debug_network_snapshot",
    description: "Capture network requests/responses from browser or Python runtime with optional filtering",
    inputSchema: {
      type: "object",
      properties: {
        runtime: {
          type: "string",
          enum: ["browser", "python"],
          description: "Target runtime to capture network from",
        },
        timeRange: {
          type: "object",
          properties: {
            since: { type: "number", description: "Start time in Unix ms" },
            until: { type: "number", description: "End time in Unix ms" },
          },
        },
        urlPattern: {
          type: "string",
          description: "Filter by URL pattern (supports * wildcard, e.g. '/api/v1/*')",
        },
        status: {
          type: "number",
          description: "Filter by HTTP status code",
        },
      },
      required: ["runtime"],
    },
  };
}

export async function handleNetworkSnapshot(
  args: NetworkSnapshotArgs
): Promise<NetworkSnapshotResult> {
  logger.info(`Network snapshot requested for runtime: ${args.runtime}`);

  validateRuntime(args.runtime);
  if (args.timeRange) validateTimeRange(args.timeRange);

  let entries: NetworkEntry[];

  if (args.runtime === "browser") {
    entries = browserRuntime.getNetworkEntries();
  } else {
    entries = await pythonRuntime.getNetworkEntries();
  }

  // Filter by time range
  if (args.timeRange) {
    entries = filterByTimeRange(entries, args.timeRange);
  }

  // Filter by URL pattern
  if (args.urlPattern) {
    entries = entries.filter((e) => matchUrlPattern(e.url, args.urlPattern!));
  }

  // Filter by status code
  if (args.status !== undefined) {
    entries = entries.filter((e) => e.status === args.status);
  }

  // Sort by timestamp ascending
  entries = entries.sort((a, b) => a.timestamp - b.timestamp);

  const now = Date.now();
  const since = args.timeRange?.since ?? (now - 3600000);
  const until = args.timeRange?.until ?? now;

  logger.debug(`Network snapshot: ${entries.length} entries returned`);

  return {
    entries,
    total: entries.length,
    timeRange: { since, until },
  };
}