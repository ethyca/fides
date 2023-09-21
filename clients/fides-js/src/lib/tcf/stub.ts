// Typescript adaptation of https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/stub

/* eslint-disable no-underscore-dangle */

interface MessageData {
  __tcfapiCall: {
    command: string;
    parameter: string | number;
    version: number;
    callId: string | number;
  };
}

const isMessageData = (data: unknown): data is MessageData =>
  typeof data === "object" && data != null && "__tcfapiCall" in data;

export const makeStub = () => {
  const TCF_LOCATOR_NAME = "__tcfapiLocator";
  const queue: any[] = [];
  const currentWindow = window;
  let frameLocator = currentWindow;
  let cmpFrame;
  let gdprApplies: boolean;

  function addFrame() {
    const doc = currentWindow.document;
    const otherCMP = !!currentWindow.frames[TCF_LOCATOR_NAME];

    if (!otherCMP) {
      if (doc.body) {
        const iframe = doc.createElement("iframe");

        iframe.style.cssText = "display:none";
        iframe.name = TCF_LOCATOR_NAME;
        doc.body.appendChild(iframe);
      } else {
        setTimeout(addFrame, 5);
      }
    }

    return !otherCMP;
  }

  function tcfAPIHandler(...args: any[]) {
    if (!args.length) {
      /**
       * shortcut to get the queue when the full CMP
       * implementation loads; it can call tcfapiHandler()
       * with no arguments to get the queued arguments
       */

      return queue;
    }
    if (args[0] === "setGdprApplies") {
      /**
       * shortcut to set gdprApplies if the publisher
       * knows that they apply GDPR rules to all
       * traffic (see the section on "What does the
       * gdprApplies value mean" for more
       */
      if (
        args.length > 3 &&
        parseInt(args[1], 10) === 2 &&
        typeof args[3] === "boolean"
      ) {
        // eslint-disable-next-line prefer-destructuring
        gdprApplies = args[3];

        if (typeof args[2] === "function") {
          args[2]("set", true);
        }
      }
    } else if (args[0] === "ping") {
      /**
       * Only supported method; give PingReturn
       * object as response
       */
      if (typeof args[2] === "function") {
        args[2]({
          gdprApplies,
          cmpLoaded: false,
          cmpStatus: "stub",
        });
      }
    } else {
      /**
       * some other method, just queue it for the
       * full CMP implementation to deal with
       */
      queue.push(args);
    }
    return null;
  }

  function postMessageEventHandler(event: MessageEvent<MessageData>) {
    const msgIsString = typeof event.data === "string";
    let json = {};

    if (msgIsString) {
      try {
        /**
         * Try to parse the data from the event.  This is important
         * to have in a try/catch because often messages may come
         * through that are not JSON
         */
        json = JSON.parse(event.data);
      } catch (ignore) {
        json = {};
        /* empty */
      }
    } else {
      json = event.data;
    }

    if (!isMessageData(json)) {
      return null;
    }

    const payload = json.__tcfapiCall;

    if (payload && window.__tcfapi) {
      window.__tcfapi(
        payload.command,
        payload.version,
        (retValue: any, success: boolean) => {
          const returnMsg = {
            __tcfapiReturn: {
              returnValue: retValue,
              success,
              callId: payload.callId,
            },
          };

          if (event && event.source && event.source.postMessage) {
            event.source.postMessage(
              msgIsString ? JSON.stringify(returnMsg) : returnMsg,
              //   @ts-ignore
              "*"
            );
          }
        },
        payload.parameter
      );
    }
    return null;
  }

  /**
   * Iterate up to the top window checking for an already-created
   * "__tcfapilLocator" frame on every level. If one exists already then we are
   * not the master CMP and will not queue commands.
   */
  while (frameLocator) {
    try {
      if (frameLocator.frames[TCF_LOCATOR_NAME]) {
        cmpFrame = frameLocator;
        break;
      }
    } catch (ignore) {
      /* empty */
    }

    // if we're at the top and no cmpFrame
    if (frameLocator === currentWindow.top) {
      break;
    }

    // Move up
    // @ts-ignore
    frameLocator = frameLocator.parent;
  }

  if (!cmpFrame) {
    // we have recur'd up the windows and have found no __tcfapiLocator frame
    addFrame();
    currentWindow.__tcfapi = tcfAPIHandler;
    currentWindow.addEventListener("message", postMessageEventHandler, false);
  }
};
