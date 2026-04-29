import type { Runtime, ConsoleLevel, TimeRange } from "../types/index.js";
export declare class ValidationError extends Error {
    constructor(message: string);
}
export declare function validateRuntime(runtime: unknown): asserts runtime is Runtime;
export declare function validateConsoleLevel(level: unknown): asserts level is ConsoleLevel;
export declare function validateTimeRange(timeRange: unknown): asserts timeRange is TimeRange;
export declare function validateString(value: unknown, fieldName: string): asserts value is string;
export declare function validateNumber(value: unknown, fieldName: string): asserts value is number;
export declare function validateArray(value: unknown, fieldName: string): asserts value is unknown[];
export declare function filterByTimeRange<T extends {
    timestamp: number;
}>(entries: T[], timeRange?: TimeRange): T[];
export declare function matchUrlPattern(url: string, pattern: string): boolean;
