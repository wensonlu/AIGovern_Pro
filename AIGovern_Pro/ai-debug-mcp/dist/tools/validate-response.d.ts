import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { ValidateResponseArgs, ValidateResponseResult } from "../types/index.js";
export declare function createValidateResponseTool(): Tool;
export declare function handleValidateResponse(args: ValidateResponseArgs): Promise<ValidateResponseResult>;
