// Validator utility for AI Debug MCP
export class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}
export function validateRuntime(runtime) {
    if (runtime !== "browser" && runtime !== "python") {
        throw new ValidationError(`Invalid runtime: ${runtime}. Expected "browser" or "python".`);
    }
}
export function validateConsoleLevel(level) {
    const validLevels = ["log", "error", "warn", "info", "debug"];
    if (level !== undefined && !validLevels.includes(level)) {
        throw new ValidationError(`Invalid console level: ${level}. Expected one of: ${validLevels.join(", ")}.`);
    }
}
export function validateTimeRange(timeRange) {
    if (timeRange === undefined)
        return;
    if (typeof timeRange !== "object" || timeRange === null) {
        throw new ValidationError("timeRange must be an object");
    }
    const tr = timeRange;
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
export function validateString(value, fieldName) {
    if (typeof value !== "string") {
        throw new ValidationError(`${fieldName} must be a string`);
    }
}
export function validateNumber(value, fieldName) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
        throw new ValidationError(`${fieldName} must be a number`);
    }
}
export function validateArray(value, fieldName) {
    if (!Array.isArray(value)) {
        throw new ValidationError(`${fieldName} must be an array`);
    }
}
export function filterByTimeRange(entries, timeRange) {
    if (!timeRange)
        return entries;
    return entries.filter((entry) => {
        if (timeRange.since !== undefined && entry.timestamp < timeRange.since)
            return false;
        if (timeRange.until !== undefined && entry.timestamp > timeRange.until)
            return false;
        return true;
    });
}
export function matchUrlPattern(url, pattern) {
    // Extract path from full URL if it looks like a URL
    let pathToMatch = url;
    try {
        const parsed = new URL(url);
        pathToMatch = parsed.pathname;
    }
    catch {
        // Not a valid URL, use as-is
    }
    if (pattern === "*" || pattern === "")
        return true;
    // Simple wildcard matching: convert /api/v1/* to regex
    const regexPattern = pattern
        .replace(/[.+?^${}()|[\]\\]/g, "\\$&") // escape regex special chars except *
        .replace(/\*/g, ".*"); // * becomes .*
    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(pathToMatch);
}
