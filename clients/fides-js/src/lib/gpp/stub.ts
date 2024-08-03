/**
 * Typescript adaptation of https://github.com/IABTechLab/iabgpp-es/blob/master/modules/stub
 * Refactored to share code with the TCF version
 */

import {
  CmpDisplayStatus,
  CmpStatus,
  PingData,
  SignalStatus,
} from "@iabgpp/cmpapi";

import { addFrame, GPP_FRAME_NAME, locateFrame } from "../cmp-stubs";
import { GppCallback, GppFunction } from "./types";

/* eslint-disable no-underscore-dangle */

interface GppEvent {
  id: number;
  callback: GppCallback;
  parameter: any;
}

interface MessageData {
  __gppCall: {
    command: string;
    parameter?: string | number;
    version: string;
    callId: string | number;
  };
}

const isMessageData = (data: unknown): data is MessageData =>
  typeof data === "object" && data != null && "__gppCall" in data;

export const makeStub = () => {
  const queue: any[] = [];
  const events: GppEvent[] = [];
  let lastId: number | undefined;

  const gppAPIHandler: GppFunction = (cmd, callback, parameter, version) => {
    if (cmd === "queue") {
      return queue;
    }

    if (cmd === "events") {
      return events;
    }

    const pingData: PingData = {
      gppVersion: "1.1", // must be “Version.Subversion”, current: “1.1”
      cmpStatus: CmpStatus.STUB, // possible values: stub, loading, loaded, error
      cmpDisplayStatus: CmpDisplayStatus.HIDDEN, // possible values: hidden, visible, disabled
      signalStatus: SignalStatus.NOT_READY, // possible values: not ready, ready
      supportedAPIs: [],
      cmpId: 0, // IAB assigned CMP ID, may be 0 during stub/loading
      sectionList: [],
      applicableSections: [0],
      gppString: "",
      parsedSections: {},
    };

    if (cmd === "ping") {
      callback(pingData, true);
    } else if (cmd === "addEventListener") {
      if (!lastId) {
        lastId = 0;
      }
      lastId += 1;
      const listenerId = lastId;
      events.push({
        id: listenerId,
        callback,
        parameter,
      });
      callback(
        {
          eventName: "listenerRegistered",
          listenerId, // Registered ID of the listener
          data: true, // positive signal
          pingData,
        },
        true,
      );
    } else if (cmd === "removeEventListener") {
      let success = false;
      // eslint-disable-next-line no-plusplus
      for (let i = 0; i < events.length; i++) {
        if (events[i].id === parameter) {
          events.splice(i, 1);
          success = true;
          break;
        }
      }
      callback(
        {
          eventName: "listenerRemoved",
          listenerId: parameter as number, // Registered ID of the listener
          data: success, // status info
          pingData,
        },
        true,
      );
    } else if (cmd === "hasSection") {
      callback(false, true);
    } else if (cmd === "getSection" || cmd === "getField") {
      callback(null, true);
    }
    // queue all other commands
    else {
      queue.push([].slice.apply([cmd, callback, parameter, version]));
    }
    return null;
  };

  const postMessageEventHandler = (event: MessageEvent<MessageData>) => {
    const msgIsString = typeof event.data === "string";
    let json = {};

    if (msgIsString) {
      try {
        json = JSON.parse(event.data);
      } catch (ignore) {
        json = {};
      }
    } else {
      json = event.data;
    }

    if (!isMessageData(json)) {
      return null;
    }

    const payload = json.__gppCall;

    if (payload && window.__gpp) {
      const i = json.__gppCall;
      window.__gpp(
        i.command,
        (retValue, success) => {
          const returnMsg = {
            __gppReturn: {
              returnValue: retValue,
              success,
              callId: i.callId,
            },
          };

          if (event && event.source && event.source.postMessage) {
            event.source.postMessage(
              msgIsString ? JSON.stringify(returnMsg) : returnMsg,
              //   @ts-ignore
              "*",
            );
          }
        },
        "parameter" in i ? i.parameter : undefined,
        "version" in i ? i.version : "1.1",
      );
    }
    return null;
  };

  const cmpFrame = locateFrame(GPP_FRAME_NAME);

  if (!cmpFrame) {
    addFrame(GPP_FRAME_NAME);
    window.__gpp = gppAPIHandler;
    window.addEventListener("message", postMessageEventHandler, false);
  }
};
