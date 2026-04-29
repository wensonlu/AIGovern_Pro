import type { ConsoleEntry, NetworkEntry } from "../types/index.js";
export declare class BrowserRuntime {
    private browser;
    private consoleBuffer;
    private networkBuffer;
    launch(): Promise<void>;
    attach(url: string): Promise<void>;
    getConsoleEntries(): ConsoleEntry[];
    getNetworkEntries(): NetworkEntry[];
    clearBuffers(): void;
    close(): Promise<void>;
}
export declare const browserRuntime: BrowserRuntime;
