import { useCallback, useEffect, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectToken } from "~/features/auth/auth.slice";

import { streamChatTurn } from "./streaming";
import type {
  ChatMessage,
  JsonRenderSpec,
  Status,
  UseFormBuilder,
  UseFormBuilderInput,
} from "./types";
import { sanitizeSpec, tryParseSpec } from "./utils";

export function useFormBuilder(input: UseFormBuilderInput): UseFormBuilder {
  const [spec, setSpec] = useState<JsonRenderSpec | null>(input.initialSpec);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const streamDoneRef = useRef<Promise<void> | null>(null);
  const messagesRef = useRef(messages);
  const specRef = useRef(spec);
  const authToken = useAppSelector(selectToken);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setStatus("aborted");
  }, []);

  useEffect(() => () => abortRef.current?.abort(), []);

  const sendMessage = useCallback(
    async (text: string) => {
      // If a stream is already running, abort it and wait for it to fully
      // finish so old event handlers don't interleave with the new stream.
      if (abortRef.current) {
        abortRef.current.abort();
        await streamDoneRef.current;
      }

      const userMessage: ChatMessage = { role: "user", content: text };
      const nextHistory = [...messagesRef.current, userMessage];
      messagesRef.current = nextHistory;
      setMessages(nextHistory);
      setStatus("streaming");
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;

      let resolveStreamDone: () => void;
      streamDoneRef.current = new Promise<void>((resolve) => {
        resolveStreamDone = resolve;
      });

      let buffer = "";
      try {
        const stream = streamChatTurn({
          propertyId: input.propertyId,
          actionPolicyKey: input.actionPolicyKey,
          currentSpec: specRef.current,
          messages: nextHistory,
          signal: controller.signal,
          authToken,
        });

        // eslint-disable-next-line no-restricted-syntax
        for await (const ev of stream) {
          if (ev.event === "chunk") {
            buffer += ev.data;
            const parsed = tryParseSpec(buffer);
            if (parsed) {
              const sanitized = sanitizeSpec(parsed);
              specRef.current = sanitized;
              setSpec(sanitized);
            }
          } else if (ev.event === "done") {
            let payload: { raw?: string } | null = null;
            try {
              payload = JSON.parse(ev.data) as { raw?: string };
            } catch {
              // structured server payload – if it isn't valid JSON, ignore it
            }
            if (payload?.raw) {
              const final = tryParseSpec(payload.raw);
              if (final) {
                const sanitized = sanitizeSpec(final);
                specRef.current = sanitized;
                setSpec(sanitized);
                const fieldCount = (final.elements?.form?.children ?? [])
                  .length;
                setMessages((prev) => {
                  const next = [
                    ...prev,
                    {
                      role: "assistant" as const,
                      content:
                        fieldCount === 1
                          ? "Updated the form (1 field)."
                          : `Updated the form (${fieldCount} fields).`,
                    },
                  ];
                  messagesRef.current = next;
                  return next;
                });
              } else {
                // No usable spec parsed — surface the raw model output so
                // the user can see whatever the LLM said.
                setMessages((prev) => {
                  const next = [
                    ...prev,
                    { role: "assistant" as const, content: payload.raw ?? "" },
                  ];
                  messagesRef.current = next;
                  return next;
                });
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
        resolveStreamDone!();
      }
    },
    [input.actionPolicyKey, input.propertyId, authToken],
  );

  return { spec, messages, status, error, sendMessage, abort, setSpec };
}
