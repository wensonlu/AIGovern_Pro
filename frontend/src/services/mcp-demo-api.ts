/**
 * MCP Demo API Client
 * Handles communication with backend MCP service
 */

interface Event {
  type: string;
  [key: string]: any;
}

/**
 * Stream AI task execution from backend
 * Returns async iterator of events
 */
export async function* streamAiTask(
  task: string,
  sessionId: string
): AsyncGenerator<Event> {
  const controller = new AbortController();
  const response = await fetch('/api/demo/ai-task', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ task, session_id: sessionId }),
    signal: controller.signal,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // Process any remaining buffered data
        if (buffer.trim()) {
          try {
            const event = JSON.parse(buffer);
            yield event;
          } catch (e) {
            console.error('Failed to parse final event:', buffer);
          }
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines (NDJSON format)
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
          const event = JSON.parse(line);
          yield event;
        } catch (e) {
          console.error('Failed to parse event:', line, e);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Get current screenshot for a session
 */
export async function getScreenshot(sessionId: string): Promise<string> {
  const response = await fetch(`/api/demo/screenshot/${sessionId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch screenshot: ${response.status}`);
  }

  const data = await response.json();
  return data.image;
}

/**
 * Reset a session
 */
export async function resetSession(sessionId: string): Promise<void> {
  const response = await fetch(`/api/demo/session/${sessionId}/reset`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to reset session: ${response.status}`);
  }
}

/**
 * Check MCP service health
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch('/api/demo/health');
    return response.ok;
  } catch {
    return false;
  }
}
