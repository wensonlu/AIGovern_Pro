// AI Debug MCP Server - Main Entry Point
// Following SPEC.md Section 4.2

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type CallToolRequest,
} from "@modelcontextprotocol/sdk/types.js";

import { logger } from "./lib/logger.js";

import {
  createConsoleSnapshotTool,
  handleConsoleSnapshot,
} from "./tools/console-snapshot.js";
import {
  createNetworkSnapshotTool,
  handleNetworkSnapshot,
} from "./tools/network-snapshot.js";
import {
  createErrorSummaryTool,
  handleErrorSummary,
} from "./tools/error-summary.js";
import {
  createValidateResponseTool,
  handleValidateResponse,
} from "./tools/validate-response.js";
import {
  createCheckErrorsTool,
  handleCheckErrors,
} from "./tools/check-errors.js";
import {
  createAssertNetworkTool,
  handleAssertNetwork,
} from "./tools/assert-network.js";
import {
  createCollectAllTool,
  handleCollectAll,
} from "./tools/collect-all.js";

import type {
  ConsoleSnapshotArgs,
  NetworkSnapshotArgs,
  ErrorSummaryArgs,
  ValidateResponseArgs,
  CheckErrorsArgs,
  AssertNetworkArgs,
  CollectAllArgs,
} from "./types/index.js";

// Create server instance
const server = new Server(
  { name: "ai-debug-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

// Register all 8 tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      createConsoleSnapshotTool(),
      createNetworkSnapshotTool(),
      createErrorSummaryTool(),
      createValidateResponseTool(),
      createCheckErrorsTool(),
      createAssertNetworkTool(),
      createCollectAllTool(),
    ],
  };
});

// Tool name to handler mapping
const toolHandlers: Record<string, (args: unknown) => Promise<unknown>> = {
  debug_console_snapshot: (args) => handleConsoleSnapshot(args as ConsoleSnapshotArgs),
  debug_network_snapshot: (args) => handleNetworkSnapshot(args as NetworkSnapshotArgs),
  debug_error_summary: (args) => handleErrorSummary(args as ErrorSummaryArgs),
  debug_validate_response: (args) => handleValidateResponse(args as ValidateResponseArgs),
  debug_check_errors: (args) => handleCheckErrors(args as CheckErrorsArgs),
  debug_assert_network: (args) => handleAssertNetwork(args as AssertNetworkArgs),
  debug_collect_all: (args) => handleCollectAll(args as CollectAllArgs),
};

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request: CallToolRequest) => {
  const { name, arguments: args } = request.params;

  logger.info(`Tool call received: ${name}`);

  const handler = toolHandlers[name];
  if (!handler) {
    logger.error(`Unknown tool: ${name}`);
    return {
      content: [
        {
          type: "text" as const,
          text: `Unknown tool: ${name}. Available tools: ${Object.keys(toolHandlers).join(", ")}`,
        },
      ],
      isError: true,
    };
  }

  try {
    const result = await handler(args ?? {});
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (err) {
    logger.error(`Tool execution failed for ${name}: ${err}`);
    const errorMessage = err instanceof Error ? err.message : String(err);
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({ error: errorMessage }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  logger.info("Starting AI Debug MCP Server...");

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("AI Debug MCP Server connected and ready");
}

main().catch((err) => {
  logger.error(`Server failed to start: ${err}`);
  process.exit(1);
});