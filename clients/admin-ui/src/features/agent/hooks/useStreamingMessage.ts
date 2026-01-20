/**
 * Hook for handling streaming messages from the agent API.
 */

import { useCallback, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";

import {
  addToolCall,
  appendStreamContent,
  resetStreamingState,
  setStreamingError,
  setToolResult,
  startStreaming,
  stopStreaming,
} from "../agent.slice";
import type { SSEEvent } from "../types";

interface UseStreamingMessageReturn {
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  cancelStream: () => void;
  isStreaming: boolean;
}

export function useStreamingMessage(): UseStreamingMessageReturn {
  const dispatch = useAppDispatch();
  const token = useAppSelector(selectToken);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (conversationId: string, content: string) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      dispatch(startStreaming());
      setIsStreaming(true);

      try {
        const headers = new Headers();
        addCommonHeaders(headers, token);
        headers.set("Content-Type", "application/json");
        headers.set("Accept", "text/event-stream");

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_FIDESCTL_API}/plus/agent/conversations/${conversationId}/messages`,
          {
            method: "POST",
            headers,
            body: JSON.stringify({ content }),
            signal: abortController.signal,
          }
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || `HTTP ${response.status}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Process complete events from buffer
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data.trim()) {
                try {
                  const event: SSEEvent = JSON.parse(data);
                  processEvent(event, dispatch);
                } catch (e) {
                  console.warn("Failed to parse SSE event:", data);
                }
              }
            }
          }
        }

        dispatch(stopStreaming());
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          // Stream was cancelled, don't treat as error
          dispatch(stopStreaming());
        } else {
          dispatch(setStreamingError((error as Error).message));
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [dispatch, token]
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    dispatch(resetStreamingState());
    setIsStreaming(false);
  }, [dispatch]);

  return {
    sendMessage,
    cancelStream,
    isStreaming,
  };
}

function processEvent(event: SSEEvent, dispatch: ReturnType<typeof useAppDispatch>) {
  switch (event.type) {
    case "message_start":
      // Message started, could track message ID if needed
      break;

    case "content_delta":
      dispatch(appendStreamContent(event.content));
      break;

    case "tool_call":
      dispatch(
        addToolCall({
          id: event.tool_call_id,
          name: event.tool_name,
          arguments: event.tool_arguments,
        })
      );
      break;

    case "tool_result":
      dispatch(
        setToolResult({
          toolCallId: event.tool_call_id,
          result: event.content,
        })
      );
      break;

    case "message_end":
      dispatch(stopStreaming());
      break;

    case "error":
      dispatch(setStreamingError(event.error));
      break;

    default:
      // Unknown event type
      break;
  }
}
