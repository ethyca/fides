export const TCF_FRAME_NAME = "__tcfapiLocator";
export const GPP_FRAME_NAME = "__gppLocator";

export type IabFrameName = typeof TCF_FRAME_NAME | typeof GPP_FRAME_NAME;

/**
 * If an iframe of `name` doesn't already exist, add it to the DOM.
 * If one exists already then we are not the master CMP and will not queue commands.
 * */
export const addFrame = (name: IabFrameName) => {
  const otherCmp = !!window.frames[name];

  if (!otherCmp) {
    if (window.document.body) {
      const iframe = window.document.createElement("iframe");
      iframe.style.cssText = "display:none";
      iframe.name = name;
      window.document.body.appendChild(iframe);
    } else {
      setTimeout(() => addFrame(name), 5);
    }
  }
};

/**
 * Iterate up to the top window checking for an already-created
 * "__tcfapilLocator" frame on every level.
 */
export const locateFrame = (name: IabFrameName) => {
  let frameLocator = window;
  let cmpFrame;
  while (frameLocator) {
    try {
      if (frameLocator.frames[name]) {
        cmpFrame = frameLocator;
        break;
      }
    } catch (ignore) {
      // empty
    }

    // if we're at the top and no cmpFrame
    if (frameLocator === window.top) {
      break;
    }
    // Move up
    // @ts-ignore
    frameLocator = frameLocator.parent;
  }
  return cmpFrame;
};
