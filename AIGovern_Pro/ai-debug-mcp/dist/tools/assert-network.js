// debug_assert_network tool
// Following SPEC.md Section 4.4.6
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import { validateRuntime, validateString, validateNumber } from "../lib/validator.js";
import { matchUrlPattern } from "../lib/validator.js";
export function createAssertNetworkTool() {
    return {
        name: "debug_assert_network",
        description: "Assert that a specific network request matches expected URL pattern and status code",
        inputSchema: {
            type: "object",
            properties: {
                runtime: {
                    type: "string",
                    enum: ["browser", "python"],
                    description: "Target runtime to assert network from",
                },
                url: {
                    type: "string",
                    description: "Exact URL or pattern with * wildcard (e.g. '/api/v1/*')",
                },
                expectedStatus: {
                    type: "number",
                    description: "Expected HTTP status code",
                },
            },
            required: ["runtime", "url", "expectedStatus"],
        },
    };
}
export async function handleAssertNetwork(args) {
    logger.info(`Assert network requested for runtime: ${args.runtime}, url=${args.url}, expectedStatus=${args.expectedStatus}`);
    validateRuntime(args.runtime);
    validateString(args.url, "url");
    validateNumber(args.expectedStatus, "expectedStatus");
    let entries;
    if (args.runtime === "browser") {
        entries = browserRuntime.getNetworkEntries();
    }
    else {
        entries = await pythonRuntime.getNetworkEntries();
    }
    // Find matching entries by URL pattern
    const matchingEntries = entries.filter((e) => matchUrlPattern(e.url, args.url));
    if (matchingEntries.length === 0) {
        return {
            url: args.url,
            expectedStatus: args.expectedStatus,
            actualStatus: null,
            matched: false,
            detail: `No network request found matching URL pattern: ${args.url}`,
        };
    }
    // Get most recent matching entry
    const mostRecent = [...matchingEntries].sort((a, b) => b.timestamp - a.timestamp)[0];
    const actualStatus = mostRecent.status;
    const matched = actualStatus === args.expectedStatus;
    let detail;
    if (matched) {
        detail = `Network request to ${mostRecent.url} returned status ${actualStatus} (expected ${args.expectedStatus}) - MATCH`;
    }
    else {
        detail = `Network request to ${mostRecent.url} returned status ${actualStatus}, expected ${args.expectedStatus} - MISMATCH`;
    }
    logger.debug(`Assert network result: ${matched ? "MATCH" : "MISMATCH"}`);
    return {
        url: args.url,
        expectedStatus: args.expectedStatus,
        actualStatus,
        matched,
        request: mostRecent,
        detail,
    };
}
