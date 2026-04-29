import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { AssertNetworkArgs, AssertNetworkResult } from "../types/index.js";
export declare function createAssertNetworkTool(): Tool;
export declare function handleAssertNetwork(args: AssertNetworkArgs): Promise<AssertNetworkResult>;
