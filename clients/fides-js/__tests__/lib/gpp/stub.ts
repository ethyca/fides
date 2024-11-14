/* eslint-disable no-underscore-dangle */
import { EventData, PingData } from "@iabgpp/cmpapi";

import { makeStub } from "../../../src/lib/gpp/stub";
import { GppCallback } from "../../../src/lib/gpp/types";

const EXPECTED_PING_DATA = {
  gppVersion: "1.1",
  cmpStatus: "stub",
  cmpDisplayStatus: "hidden",
  signalStatus: "not ready",
  supportedAPIs: [],
  cmpId: 0,
  sectionList: [],
  applicableSections: [0],
  gppString: "",
  parsedSections: {},
};

describe("makeStub", () => {
  it("can make stub functions", () => {
    makeStub();
    expect(window.__gpp).toBeTruthy();
    const gppCall = window.__gpp!;

    // Check 'queue' and 'events'
    const queue = gppCall("queue", jest.fn());
    const events = gppCall("events", jest.fn());
    expect(queue).toEqual([]);
    expect(events).toEqual([]);

    // Check 'ping'
    gppCall("ping", (data, success) => {
      expect(success).toBe(true);
      const pingData = data as PingData;
      expect(pingData).toEqual(EXPECTED_PING_DATA);
    });

    // Check 'addEventListener' and that it updates the `events` obj
    const expectedListenerId = 1;
    const addEventListener: GppCallback = (evt, success) => {
      expect(success).toBe(true);
      const eventData = evt as EventData;
      expect(eventData.listenerId).toEqual(expectedListenerId);
      expect(eventData.eventName).toEqual("listenerRegistered");
      expect(eventData.data).toBe(true);
      expect(eventData.pingData).toEqual(EXPECTED_PING_DATA);
    };
    gppCall("addEventListener", addEventListener);
    const updatedEvents = gppCall("events", jest.fn());
    expect(updatedEvents).toEqual([
      {
        id: expectedListenerId,
        callback: addEventListener,
        parameter: undefined,
      },
    ]);

    // Check 'removeEventListener' and that it updates the `events` obj
    const removeEventListener: GppCallback = (evt, success) => {
      expect(success).toBe(true);
      const eventData = evt as EventData;
      expect(eventData.listenerId).toEqual(expectedListenerId);
      expect(eventData.eventName).toEqual("listenerRemoved");
      expect(eventData.data).toBe(true);
      expect(eventData.pingData).toEqual(EXPECTED_PING_DATA);
    };
    gppCall("removeEventListener", removeEventListener, expectedListenerId);
    expect(gppCall("events", jest.fn())).toEqual([]);

    // hasSection
    gppCall(
      "hasSection",
      (data, success) => {
        expect(success).toBe(true);
        expect(data).toBe(false);
      },
      "tcfca",
    );

    // getSection
    gppCall(
      "getField",
      (data, success) => {
        expect(success).toBe(true);
        expect(data).toBe(null);
      },
      "tcfca",
    );

    // getField
    gppCall(
      "getField",
      (data, success) => {
        expect(success).toBe(true);
        expect(data).toBe(null);
      },
      "tcfca.LastUpdated",
    );
  });
});
