export interface SseEvent {
  event: string;
  data: string;
}

export async function* parseSseStream(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SseEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      // Sequential reads are required: each chunk depends on draining the
      // previous one, so concurrent reads would interleave SSE frames.
      // eslint-disable-next-line no-await-in-loop
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });

      let delimiter = buffer.indexOf("\n\n");
      while (delimiter !== -1) {
        const raw = buffer.slice(0, delimiter);
        buffer = buffer.slice(delimiter + 2);

        let event = "message";
        const dataLines: string[] = [];
        raw.split("\n").forEach((line) => {
          if (line.startsWith("event: ")) {
            event = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            dataLines.push(line.slice(6));
          }
        });
        if (dataLines.length > 0) {
          yield { event, data: dataLines.join("\n") };
        }
        delimiter = buffer.indexOf("\n\n");
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export interface ChatTurnInput {
  propertyId: string;
  actionPolicyKey: string;
  currentSpec: unknown | null;
  messages: { role: "user" | "assistant" | "system"; content: string }[];
  signal: AbortSignal;
  authToken?: string | null;
}

export async function* streamChatTurn(
  input: ChatTurnInput,
): AsyncGenerator<SseEvent> {
  const headers: Record<string, string> = {
    "content-type": "application/json",
  };
  if (input.authToken) {
    headers.authorization = `Bearer ${input.authToken}`;
  }

  const response = await fetch(
    `/api/v1/plus/property/${input.propertyId}/form-builder/chat`,
    {
      method: "POST",
      headers,
      credentials: "include",
      body: JSON.stringify({
        action_policy_key: input.actionPolicyKey,
        current_spec: input.currentSpec,
        messages: input.messages,
      }),
      signal: input.signal,
    },
  );

  if (!response.ok || !response.body) {
    const MAX_BODY_LENGTH = 500;
    let detail = "";
    try {
      const text = await response.text();
      try {
        const json = JSON.parse(text);
        detail = typeof json.detail === "string" ? json.detail : text;
      } catch {
        detail = text;
      }
    } catch {
      // body unreadable, leave detail empty
    }
    if (detail.length > MAX_BODY_LENGTH) {
      detail = `${detail.slice(0, MAX_BODY_LENGTH)}…`;
    }
    const suffix = detail ? `: ${detail}` : "";
    throw new Error(
      `Form builder chat failed: HTTP ${response.status}${suffix}`,
    );
  }

  yield* parseSseStream(response.body);
}
