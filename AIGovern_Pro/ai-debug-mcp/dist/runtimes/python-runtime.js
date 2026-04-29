// Python Runtime Adapter - HTTP Client for Python SDK
// Following SPEC.md Section 4.6
import { logger } from "../lib/logger.js";
const PYTHON_SDK_BASE_URL = "http://127.0.0.1:9310";
const TIMEOUT_MS = 2000;
export class PythonRuntime {
    baseUrl;
    constructor(baseUrl = PYTHON_SDK_BASE_URL) {
        this.baseUrl = baseUrl;
    }
    async fetch(endpoint, since) {
        const url = new URL(`${this.baseUrl}${endpoint}`);
        if (since !== undefined) {
            url.searchParams.set("since", String(since));
        }
        logger.debug(`Python SDK HTTP request: ${url.toString()}`);
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);
            const response = await fetch(url.toString(), {
                signal: controller.signal,
                headers: { "Accept": "application/json" },
            });
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        }
        catch (err) {
            if (err instanceof Error && err.name === "AbortError") {
                throw new Error(`Python SDK request timeout (${TIMEOUT_MS}ms) for ${endpoint}`);
            }
            throw err;
        }
    }
    async getConsoleEntries(since) {
        try {
            const entries = await this.fetch("/console", since);
            return entries.map((e) => ({ ...e, runtime: "python" }));
        }
        catch (err) {
            logger.error(`Failed to fetch Python console entries: ${err}`);
            return [];
        }
    }
    async getNetworkEntries(since) {
        try {
            const entries = await this.fetch("/network", since);
            return entries.map((e) => ({ ...e, runtime: "python" }));
        }
        catch (err) {
            logger.error(`Failed to fetch Python network entries: ${err}`);
            return [];
        }
    }
    async getErrorSummary() {
        try {
            const [consoleEntries, networkEntries] = await Promise.all([
                this.getConsoleEntries(),
                this.getNetworkEntries(),
            ]);
            const errors = consoleEntries.filter((e) => e.level === "error");
            const networkFails = networkEntries.filter((e) => e.status >= 400);
            return { errors, networkFails };
        }
        catch (err) {
            logger.error(`Failed to fetch Python error summary: ${err}`);
            return { errors: [], networkFails: [] };
        }
    }
}
// Singleton instance
export const pythonRuntime = new PythonRuntime();
