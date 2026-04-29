// jsdom does not expose Web Streams or TextEncoder/TextDecoder by default.
// Pull them from Node's stream/web + util before importing the module under test.
import { ReadableStream as NodeReadableStream } from "node:stream/web";
import { TextDecoder as NodeTextDecoder, TextEncoder as NodeTextEncoder } from "node:util";

if (typeof globalThis.TextEncoder === "undefined") {
  (globalThis as unknown as { TextEncoder: typeof NodeTextEncoder }).TextEncoder =
    NodeTextEncoder;
}
if (typeof globalThis.TextDecoder === "undefined") {
  (globalThis as unknown as { TextDecoder: typeof NodeTextDecoder }).TextDecoder =
    NodeTextDecoder as unknown as typeof NodeTextDecoder;
}
if (typeof globalThis.ReadableStream === "undefined") {
  (globalThis as unknown as { ReadableStream: typeof NodeReadableStream }).ReadableStream =
    NodeReadableStream;
}

import { parseSseStream } from "../streaming";

const encoder = new TextEncoder();

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      chunks.forEach((c) => controller.enqueue(encoder.encode(c)));
      controller.close();
    },
  });
}

describe("parseSseStream", () => {
  it("yields events split by blank-line delimiter", async () => {
    const stream = makeStream([
      "event: chunk\ndata: hello \n\nevent: chunk\ndata: world\n\nevent: done\ndata: {}\n\n",
    ]);

    const events: { event: string; data: string }[] = [];
    for await (const ev of parseSseStream(stream)) {
      events.push(ev);
    }

    expect(events).toEqual([
      { event: "chunk", data: "hello " },
      { event: "chunk", data: "world" },
      { event: "done", data: "{}" },
    ]);
  });

  it("buffers across chunks that split mid-event", async () => {
    const stream = makeStream([
      "event: chunk\nda",
      "ta: hello\n\nevent: done\ndata: {}\n\n",
    ]);

    const events: { event: string; data: string }[] = [];
    for await (const ev of parseSseStream(stream)) {
      events.push(ev);
    }

    expect(events).toEqual([
      { event: "chunk", data: "hello" },
      { event: "done", data: "{}" },
    ]);
  });
});
