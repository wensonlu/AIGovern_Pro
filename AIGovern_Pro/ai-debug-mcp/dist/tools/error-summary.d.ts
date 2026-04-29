import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { ErrorSummaryArgs, ErrorSummaryResult } from "../types/index.js";
export declare function createErrorSummaryTool(): Tool;
export declare function handleErrorSummary(args: ErrorSummaryArgs): Promise<ErrorSummaryResult>;
