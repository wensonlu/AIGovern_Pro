import type { ConsoleEntry, NetworkEntry } from "../types/index.js";
export declare class PythonRuntime {
    private baseUrl;
    constructor(baseUrl?: string);
    private fetch;
    getConsoleEntries(since?: number): Promise<ConsoleEntry[]>;
    getNetworkEntries(since?: number): Promise<NetworkEntry[]>;
    getErrorSummary(): Promise<{
        errors: ConsoleEntry[];
        networkFails: NetworkEntry[];
    }>;
}
export declare const pythonRuntime: PythonRuntime;
