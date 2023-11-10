// Typescript adaptation of https://github.com/IABTechLab/iabgpp-es/blob/master/modules/stub

/* eslint-disable no-underscore-dangle */

const GPP_LOCATOR_NAME = "__gppLocator";

export const makeStub = () => {
  const addFrame = () => {
    if (!window.frames[GPP_LOCATOR_NAME]) {
      if (document.body) {
        const i = document.createElement("iframe");
        i.style.cssText = "display:none";
        i.name = GPP_LOCATOR_NAME;
        document.body.appendChild(i);
      } else {
        window.setTimeout(addFrame, 10);
      }
    }
  };

  const gppAPIHandler = () => {
    const b = arguments;
    __gpp.queue = __gpp.queue || [];
    __gpp.events = __gpp.events || [];

    if (!b.length || (b.length == 1 && b[0] == "queue")) {
      return __gpp.queue;
    }

    if (b.length == 1 && b[0] == "events") {
      return __gpp.events;
    }

    const cmd = b[0];
    const clb = b.length > 1 ? b[1] : null;
    const par = b.length > 2 ? b[2] : null;
    if (cmd === "ping") {
      clb(
        {
          gppVersion: "1.1", // must be “Version.Subversion”, current: “1.1”
          cmpStatus: "stub", // possible values: stub, loading, loaded, error
          cmpDisplayStatus: "hidden", // possible values: hidden, visible, disabled
          signalStatus: "not ready", // possible values: not ready, ready
          supportedAPIs: [
            "2:tcfeuv2",
            "5:tcfcav1",
            "6:uspv1",
            "7:usnatv1",
            "8:uscav1",
            "9:usvav1",
            "10:uscov1",
            "11:usutv1",
            "12:usctv1",
          ], // list of supported APIs
          cmpId: 0, // IAB assigned CMP ID, may be 0 during stub/loading
          sectionList: [],
          applicableSections: [],
          gppString: "",
          parsedSections: {},
        },
        true
      );
    } else if (cmd === "addEventListener") {
      if (!("lastId" in __gpp)) {
        __gpp.lastId = 0;
      }
      __gpp.lastId++;
      const lnr = __gpp.lastId;
      __gpp.events.push({
        id: lnr,
        callback: clb,
        parameter: par,
      });
      clb(
        {
          eventName: "listenerRegistered",
          listenerId: lnr, // Registered ID of the listener
          data: true, // positive signal
          pingData: {
            gppVersion: "1.1", // must be “Version.Subversion”, current: “1.1”
            cmpStatus: "stub", // possible values: stub, loading, loaded, error
            cmpDisplayStatus: "hidden", // possible values: hidden, visible, disabled
            signalStatus: "not ready", // possible values: not ready, ready
            supportedAPIs: [
              "2:tcfeuv2",
              "5:tcfcav1",
              "6:uspv1",
              "7:usnatv1",
              "8:uscav1",
              "9:usvav1",
              "10:uscov1",
              "11:usutv1",
              "12:usctv1",
            ], // list of supported APIs
            cmpId: 0, // IAB assigned CMP ID, may be 0 during stub/loading
            sectionList: [],
            applicableSections: [],
            gppString: "",
            parsedSections: {},
          },
        },
        true
      );
    } else if (cmd === "removeEventListener") {
      let success = false;
      for (let i = 0; i < __gpp.events.length; i++) {
        if (__gpp.events[i].id == par) {
          __gpp.events.splice(i, 1);
          success = true;
          break;
        }
      }
      clb(
        {
          eventName: "listenerRemoved",
          listenerId: par, // Registered ID of the listener
          data: success, // status info
          pingData: {
            gppVersion: "1.1", // must be “Version.Subversion”, current: “1.1”
            cmpStatus: "stub", // possible values: stub, loading, loaded, error
            cmpDisplayStatus: "hidden", // possible values: hidden, visible, disabled
            signalStatus: "not ready", // possible values: not ready, ready
            supportedAPIs: [
              "2:tcfeuv2",
              "5:tcfcav1",
              "6:uspv1",
              "7:usnatv1",
              "8:uscav1",
              "9:usvav1",
              "10:uscov1",
              "11:usutv1",
              "12:usctv1",
            ], // list of supported APIs
            cmpId: 0, // IAB assigned CMP ID, may be 0 during stub/loading
            sectionList: [],
            applicableSections: [],
            gppString: "",
            parsedSections: {},
          },
        },
        true
      );
    } else if (cmd === "hasSection") {
      clb(false, true);
    } else if (cmd === "getSection" || cmd === "getField") {
      clb(null, true);
    }
    // queue all other commands
    else {
      __gpp.queue.push([].slice.apply(b));
    }
  };
  const postMessageEventHandler = (event: MessageEvent<any>) => {
    const msgIsString = typeof event.data === "string";
    try {
      var json = msgIsString ? JSON.parse(event.data) : event.data;
    } catch (e) {
      var json = null;
    }
    if (typeof json === "object" && json !== null && "__gppCall" in json) {
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
          event.source.postMessage(
            msgIsString ? JSON.stringify(returnMsg) : returnMsg,
            "*"
          );
        },
        "parameter" in i ? i.parameter : null,
        "version" in i ? i.version : "1.1"
      );
    }
  };
  if (!("__gpp" in window) || typeof window.__gpp !== "function") {
    addFrame();
    window.__gpp = gppAPIHandler;
    window.addEventListener("message", postMessageEventHandler, false);
  }
};
