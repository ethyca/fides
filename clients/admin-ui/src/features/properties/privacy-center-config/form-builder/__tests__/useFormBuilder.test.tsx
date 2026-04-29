import { act, renderHook } from "@testing-library/react";

import { useFormBuilder } from "../useFormBuilder";

const mockStreamChatTurn = jest.fn();

jest.mock("../streaming", () => ({
  ...jest.requireActual("../streaming"),
  streamChatTurn: (...args: unknown[]) => mockStreamChatTurn(...args),
}));

async function* fakeEvents() {
  yield { event: "chunk", data: '{"root":"form","elements":{' };
  yield { event: "chunk", data: '"form":{"type":"Form","props":{},"children":[]}' };
  yield { event: "chunk", data: "}}" };
  yield {
    event: "done",
    data: JSON.stringify({
      raw: '{"root":"form","elements":{"form":{"type":"Form","props":{},"children":[]}}}',
    }),
  };
}

beforeEach(() => {
  mockStreamChatTurn.mockReturnValue(fakeEvents());
});

describe("useFormBuilder", () => {
  it("starts idle and transitions to streaming → idle on a turn", async () => {
    const { result } = renderHook(() =>
      useFormBuilder({
        propertyId: "p1",
        actionPolicyKey: "default_access_policy",
        initialSpec: null,
      }),
    );

    expect(result.current.status).toBe("idle");

    await act(async () => {
      await result.current.sendMessage("Add a Form");
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.spec?.root).toBe("form");
    expect(result.current.messages.at(-1)?.role).toBe("assistant");
  });

  it("supports abort", async () => {
    const { result } = renderHook(() =>
      useFormBuilder({
        propertyId: "p1",
        actionPolicyKey: "default_access_policy",
        initialSpec: null,
      }),
    );

    await act(async () => {
      const promise = result.current.sendMessage("Add a Form");
      result.current.abort();
      await promise;
    });

    expect(["idle", "aborted"]).toContain(result.current.status);
  });
});
