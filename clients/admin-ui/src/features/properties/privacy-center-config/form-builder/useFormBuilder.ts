import { useCallback, useEffect, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth/auth.slice";

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

// Strip ```json … ``` fences and return the first balanced {...} object
// the LLM wrote. Falls back to the original string if no braces are found.
const extractJson = (raw: string): string => {
  let body = raw.trim();
  const fence = body.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```$/);
  if (fence) {
    body = fence[1].trim();
  }

  const firstBrace = body.indexOf("{");
  if (firstBrace === -1) {
    return body;
  }

  let depth = 0;
  let inString = false;
  let escape = false;
  for (let i = firstBrace; i < body.length; i += 1) {
    const ch = body[i];
    if (escape) {
      escape = false;
    } else if (ch === "\\") {
      escape = true;
    } else if (ch === '"') {
      inString = !inString;
    } else if (!inString) {
      if (ch === "{") {
        depth += 1;
      } else if (ch === "}") {
        depth -= 1;
        if (depth === 0) {
          return body.slice(firstBrace, i + 1);
        }
      }
    }
  }
  return body.slice(firstBrace);
};

const tryParse = (raw: string): JsonRenderSpec | null => {
  try {
    return JSON.parse(extractJson(raw)) as JsonRenderSpec;
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
  const authToken = useAppSelector(selectToken);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setStatus("aborted");
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  const sendMessage = useCallback(
    async (text: string) => {
      const userMessage: ChatMessage = { role: "user", content: text };
      const nextHistory = [...messages, userMessage];
      setMessages(nextHistory);
      setStatus("streaming");
      setError(null);

      abortRef.current?.abort();
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
          authToken,
        });

        // eslint-disable-next-line no-restricted-syntax
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
                const fieldCount = (final.elements?.form?.children ?? [])
                  .length;
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content:
                      fieldCount === 1
                        ? "Updated the form (1 field)."
                        : `Updated the form (${fieldCount} fields).`,
                  },
                ]);
              } else {
                // No usable spec parsed — surface the raw model output so
                // the user can see whatever the LLM said.
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: payload.raw ?? "" },
                ]);
              }
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
    [input.actionPolicyKey, input.propertyId, messages, spec, authToken],
  );

  return { spec, messages, status, error, sendMessage, abort, setSpec };
}
