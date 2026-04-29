import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { CollectAllArgs, CollectAllResult } from "../types/index.js";
export declare function createCollectAllTool(): Tool;
export declare function handleCollectAll(args: CollectAllArgs): Promise<CollectAllResult>;
