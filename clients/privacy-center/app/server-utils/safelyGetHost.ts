export function safelyGetHost(urlString: string = "") {
  if (urlString.length > 0) {
    try {
      return new URL(urlString).host;
    } catch (ex) {
      return "";
    }
  }

  return "";
}
