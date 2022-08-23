export const capitalize = (text: string): string =>
  text.replace(/^\w/, (c) => c.toUpperCase());

export const debounce = (fn: Function, ms = 0) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  // eslint-disable-next-line func-names
  return function (this: any, ...args: any[]) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), ms);
  };
};

export const utf8ToB64 = (str: string): string =>
  window.btoa(unescape(encodeURIComponent(str)));
