import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { NetworkSnapshotArgs, NetworkSnapshotResult } from "../types/index.js";
export declare function createNetworkSnapshotTool(): Tool;
export declare function handleNetworkSnapshot(args: NetworkSnapshotArgs): Promise<NetworkSnapshotResult>;
