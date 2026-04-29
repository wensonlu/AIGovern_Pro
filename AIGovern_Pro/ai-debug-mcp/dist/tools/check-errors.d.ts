import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { CheckErrorsArgs, CheckErrorsResult } from "../types/index.js";
export declare function createCheckErrorsTool(): Tool;
export declare function handleCheckErrors(args: CheckErrorsArgs): Promise<CheckErrorsResult>;
