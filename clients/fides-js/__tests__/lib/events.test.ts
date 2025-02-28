import { userEvent } from "@testing-library/user-event";

import { dispatchFidesEvent } from "../../src/lib/events";

describe("events", () => {
  beforeEach(() => {
    const noop = () => {};
    window.fidesDebugger = noop;
  });

  afterEach(() => {
    window.fidesDebugger =
      undefined as unknown as (typeof window)["fidesDebugger"];
  });

  describe("can have a listener for FidesUIChanged", () => {
    let listenerPromise: Promise<CustomEvent>;
    let listener: (event: CustomEvent) => void;

    beforeEach(() => {
      listenerPromise = new Promise<CustomEvent>((resolve) => {
        listener = (event: CustomEvent) => {
          resolve(event);
        };
        window.addEventListener("FidesUIChanged", listener);
      });
    });

    afterEach(() => {
      window.removeEventListener("FidesUIChanged", listener);
    });

    test("that by default fires from window", async () => {
      dispatchFidesEvent(
        "FidesUIChanged",
        {
          consent: {},
          fides_meta: {},
          identity: {},
          tcf_consent: {},
        },
        false,
      );
      const event = await listenerPromise;
      expect(event.target).toEqual(window);
    });

    describe("event bubbling", () => {
      let button: HTMLButtonElement;
      let buttonListener: (event: MouseEvent) => void;
      beforeEach(() => {
        button = document.createElement("button");
        button.setAttribute("id", "test-id");

        buttonListener = (event: MouseEvent): void => {
          dispatchFidesEvent(
            "FidesUIChanged",
            {
              consent: {},
              fides_meta: {},
              identity: {},
              tcf_consent: {},
            },
            false,
            undefined,
            event.target,
          );
        };
        button.addEventListener("click", buttonListener);
      });

      afterEach(() => {
        button.removeEventListener("click", buttonListener);
      });

      test("that an event can be fired by a different target", async () => {
        document.body.append(button);
        await userEvent.click(button);

        const event = await listenerPromise;
        expect((event.target as HTMLButtonElement).id).toEqual("test-id");
      });
    });
  });
});
