// Validator utility for Agent Observe MCP

import type {
  Runtime,
  ConsoleLevel,
  TimeRange,
} from "../types/index.js";

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

export function validateRuntime(runtime: unknown): asserts runtime is Runtime {
  if (runtime !== "browser" && runtime !== "python") {
    throw new ValidationError(`Invalid runtime: ${runtime}. Expected "browser" or "python".`);
  }
}

export function validateConsoleLevel(level: unknown): asserts level is ConsoleLevel {
  const validLevels: ConsoleLevel[] = ["log", "error", "warn", "info", "debug"];
  if (level !== undefined && !validLevels.includes(level as ConsoleLevel)) {
    throw new ValidationError(
      `Invalid console level: ${level}. Expected one of: ${validLevels.join(", ")}.`
    );
  }
}

export function validateTimeRange(timeRange: unknown): asserts timeRange is TimeRange {
  if (timeRange === undefined) return;
  if (typeof timeRange !== "object" || timeRange === null) {
    throw new ValidationError("timeRange must be an object");
  }
  const tr = timeRange as TimeRange;
  if (tr.since !== undefined && typeof tr.since !== "number") {
    throw new ValidationError("timeRange.since must be a number (Unix ms)");
  }
  if (tr.until !== undefined && typeof tr.until !== "number") {
    throw new ValidationError("timeRange.until must be a number (Unix ms)");
  }
  if (tr.since !== undefined && tr.until !== undefined && tr.since > tr.until) {
    throw new ValidationError("timeRange.since must be less than or equal to timeRange.until");
  }
}

export function validateString(value: unknown, fieldName: string): asserts value is string {
  if (typeof value !== "string") {
    throw new ValidationError(`${fieldName} must be a string`);
  }
}

export function validateNumber(value: unknown, fieldName: string): asserts value is number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ValidationError(`${fieldName} must be a number`);
  }
}

export function validateArray(value: unknown, fieldName: string): asserts value is unknown[] {
  if (!Array.isArray(value)) {
    throw new ValidationError(`${fieldName} must be an array`);
  }
}

export function filterByTimeRange<T extends { timestamp: number }>(
  entries: T[],
  timeRange?: TimeRange
): T[] {
  if (!timeRange) return entries;
  return entries.filter((entry) => {
    if (timeRange.since !== undefined && entry.timestamp < timeRange.since) return false;
    if (timeRange.until !== undefined && entry.timestamp > timeRange.until) return false;
    return true;
  });
}

export function matchUrlPattern(url: string, pattern: string): boolean {
  // Extract path from full URL if it looks like a URL
  let pathToMatch = url;
  try {
    const parsed = new URL(url);
    pathToMatch = parsed.pathname;
  } catch {
    // Not a valid URL, use as-is
  }
  
  if (pattern === "*" || pattern === "") return true;
  // Simple wildcard matching: convert /api/v1/* to regex
  const regexPattern = pattern
    .replace(/[.+?^${}()|[\]\\]/g, "\\$&")  // escape regex special chars except *
    .replace(/\*/g, ".*");  // * becomes .*
  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(pathToMatch);
}