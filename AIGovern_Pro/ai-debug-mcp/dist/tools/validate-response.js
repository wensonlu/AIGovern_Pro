// debug_validate_response tool
// Following SPEC.md Section 4.4.4
import { browserRuntime } from "../runtimes/browser-runtime.js";
import { pythonRuntime } from "../runtimes/python-runtime.js";
import { logger } from "../lib/logger.js";
import { validateRuntime, validateArray } from "../lib/validator.js";
function extractFields(body) {
    if (!body || typeof body !== "object")
        return [];
    const fields = [];
    const obj = body;
    function traverse(value, prefix = "") {
        if (value !== null && typeof value === "object") {
            if (Array.isArray(value)) {
                // For arrays, traverse the first element to get field names
                // but also add the array field name itself
                if (prefix)
                    fields.push(prefix);
                if (value.length > 0) {
                    traverse(value[0], prefix);
                }
            }
            else {
                // For objects, add the key and recurse
                for (const [key, val] of Object.entries(value)) {
                    const newKey = prefix ? `${prefix}.${key}` : key;
                    fields.push(newKey);
                    traverse(val, newKey);
                }
            }
        }
    }
    traverse(obj);
    return [...new Set(fields)].sort();
}
export function createValidateResponseTool() {
    return {
        name: "debug_validate_response",
        description: "Validate that a network response contains all expected fields",
        inputSchema: {
            type: "object",
            properties: {
                runtime: {
                    type: "string",
                    enum: ["browser", "python"],
                    description: "Target runtime to validate response from",
                },
                expectedFields: {
                    type: "array",
                    items: { type: "string" },
                    description: "List of expected field names (e.g. ['token', 'userId', 'expiresAt'])",
                },
                responseId: {
                    type: "string",
                    description: "Specific response URL/id to validate. If not provided, uses the most recent response",
                },
            },
            required: ["runtime", "expectedFields"],
        },
    };
}
export async function handleValidateResponse(args) {
    logger.info(`Validate response requested for runtime: ${args.runtime}`);
    validateRuntime(args.runtime);
    validateArray(args.expectedFields, "expectedFields");
    let entries;
    if (args.runtime === "browser") {
        entries = browserRuntime.getNetworkEntries();
    }
    else {
        entries = await pythonRuntime.getNetworkEntries();
    }
    // Filter to only successful responses (2xx)
    const successfulEntries = entries.filter((e) => e.status >= 200 && e.status < 300);
    if (successfulEntries.length === 0) {
        return {
            responseId: args.responseId ?? "none",
            validated: false,
            expectedFields: args.expectedFields,
            presentFields: [],
            missingFields: [...args.expectedFields],
            extraFields: [],
            detail: "No successful (2xx) responses found in buffer",
        };
    }
    // Find the target response or use the most recent
    let targetEntry;
    if (args.responseId) {
        targetEntry = entries.find((e) => e.id === args.responseId || e.url === args.responseId)
            ?? successfulEntries[successfulEntries.length - 1];
    }
    else {
        // Sort by timestamp descending, take most recent
        targetEntry = [...successfulEntries].sort((a, b) => b.timestamp - a.timestamp)[0];
    }
    // Extract fields from response body
    const presentFields = extractFields(targetEntry.responseBody);
    // Compute missing and extra
    const expectedSet = new Set(args.expectedFields);
    const presentSet = new Set(presentFields);
    const missingFields = args.expectedFields.filter((f) => !presentSet.has(f));
    const extraFields = presentFields.filter((f) => !expectedSet.has(f));
    const validated = missingFields.length === 0;
    const detail = validated
        ? `Response ${targetEntry.id} contains all expected fields`
        : `Response ${targetEntry.id} missing fields: ${missingFields.join(", ")}`;
    logger.debug(`Validation result: ${validated ? "PASS" : "FAIL"} - ${detail}`);
    return {
        responseId: targetEntry.id,
        validated,
        expectedFields: args.expectedFields,
        presentFields,
        missingFields,
        extraFields,
        detail,
    };
}
