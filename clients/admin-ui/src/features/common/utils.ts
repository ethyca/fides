// eslint-disable-next-line import/prefer-default-export
export function capitalize(text: string): string {
  return text.replace(/^\w/, (c) => c.toUpperCase());
}

// eslint-disable-next-line import/prefer-default-export
export function utf8ToB64(str: string): string {
  return window.btoa(unescape(encodeURIComponent(str)));
}
