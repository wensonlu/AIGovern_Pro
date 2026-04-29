// debug_check_errors tool
// Following SPEC.md Section 4.4.5

import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type {
  CheckErrorsArgs,
  CheckErrorsResult,
  ErrorEntry,
  ConsoleEntry,
} from "../types/index.js";
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import { validateRuntime, validateArray } from "../lib/validator.js";

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

export function createCheckErrorsTool(): Tool {
  return {
    name: "debug_check_errors",
    description: "Check if specific error patterns are found in console errors",
    inputSchema: {
      type: "object",
      properties: {
        runtime: {
          type: "string",
          enum: ["browser", "python"],
          description: "Target runtime to check errors from",
        },
        sessionId: {
          type: "string",
          description: "Browser session id from debug_browser_attach (only used when runtime=browser)",
        },
        expectedErrors: {
          type: "array",
          items: { type: "string" },
          description: "List of error keywords to look for (e.g. ['TypeError', 'Cannot read'])",
        },
      },
      required: ["runtime", "expectedErrors"],
    },
  };
}

export async function handleCheckErrors(args: CheckErrorsArgs): Promise<CheckErrorsResult> {
  logger.info(`Check errors requested for runtime: ${args.runtime}`);

  validateRuntime(args.runtime);
  validateArray(args.expectedErrors, "expectedErrors");

  let consoleEntries: ConsoleEntry[];

  if (args.runtime === "browser") {
    consoleEntries = await browserRuntime.getConsoleEntries(args.sessionId);
  } else {
    consoleEntries = await pythonRuntime.getConsoleEntries();
  }

  // Get only error level entries
  const errorEntries = consoleEntries.filter((e) => e.level === "error");
  const deduplicatedErrors = deduplicateErrors(errorEntries);

  // Check which expected errors match
  const matchedErrors: string[] = [];
  const unmatchedErrors: string[] = [];
  const foundErrors: ErrorEntry[] = [];

  for (const expected of args.expectedErrors) {
    const matchingEntry = deduplicatedErrors.find(
      (e) => e.message.includes(expected) || (e.stack && e.stack.includes(expected))
    );

    if (matchingEntry) {
      matchedErrors.push(expected);
      if (!foundErrors.some((fe) => fe.message === matchingEntry.message)) {
        foundErrors.push(matchingEntry);
      }
    } else {
      unmatchedErrors.push(expected);
    }
  }

  const matched = unmatchedErrors.length === 0 && matchedErrors.length > 0;

  logger.debug(
    `Check errors result: matched=${matched}, matchedPatterns=${matchedErrors.join(", ")}`
  );

  return {
    matched,
    matchedErrors,
    unmatchedErrors,
    foundErrors,
  };
}
