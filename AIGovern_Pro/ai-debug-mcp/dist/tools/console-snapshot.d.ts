import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { ConsoleSnapshotArgs, ConsoleSnapshotResult } from "../types/index.js";
export declare function createConsoleSnapshotTool(): Tool;
export declare function handleConsoleSnapshot(args: ConsoleSnapshotArgs): Promise<ConsoleSnapshotResult>;
