import { useCallback, useRef, useState } from "react";

import type { JsonRenderSpec } from "./mapper";
import { streamChatTurn } from "./streaming";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export type Status = "idle" | "streaming" | "aborted" | "error";

interface UseFormBuilderInput {
  propertyId: string;
  actionPolicyKey: string;
  initialSpec: JsonRenderSpec | null;
}

export interface UseFormBuilder {
  spec: JsonRenderSpec | null;
  messages: ChatMessage[];
  status: Status;
  error: string | null;
  sendMessage: (text: string) => Promise<void>;
  abort: () => void;
  setSpec: (spec: JsonRenderSpec | null) => void;
}

const tryParse = (raw: string): JsonRenderSpec | null => {
  try {
    return JSON.parse(raw) as JsonRenderSpec;
  } catch {
    return null;
  }
};

export function useFormBuilder(input: UseFormBuilderInput): UseFormBuilder {
  const [spec, setSpec] = useState<JsonRenderSpec | null>(input.initialSpec);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setStatus("aborted");
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMessage: ChatMessage = { role: "user", content: text };
      const nextHistory = [...messages, userMessage];
      setMessages(nextHistory);
      setStatus("streaming");
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;

      let buffer = "";
      try {
        const stream = streamChatTurn({
          propertyId: input.propertyId,
          actionPolicyKey: input.actionPolicyKey,
          currentSpec: spec,
          messages: nextHistory,
          signal: controller.signal,
        });

        for await (const ev of stream) {
          if (ev.event === "chunk") {
            buffer += ev.data;
            const parsed = tryParse(buffer);
            if (parsed) {
              setSpec(parsed);
            }
          } else if (ev.event === "done") {
            const payload = tryParse(ev.data) as { raw?: string } | null;
            if (payload?.raw) {
              const final = tryParse(payload.raw);
              if (final) {
                setSpec(final);
              }
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: payload.raw ?? "" },
              ]);
            }
          } else if (ev.event === "error") {
            setError(ev.data);
            setStatus("error");
            return;
          }
        }
        setStatus("idle");
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          setStatus("aborted");
          return;
        }
        setError((err as Error).message);
        setStatus("error");
      } finally {
        abortRef.current = null;
      }
    },
    [input.actionPolicyKey, input.propertyId, messages, spec],
  );

  return { spec, messages, status, error, sendMessage, abort, setSpec };
}
