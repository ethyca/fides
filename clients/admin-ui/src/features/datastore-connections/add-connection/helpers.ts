/**
 * Format the connection key to be lower case and replace spaces and '.' with underscores
 * @param key Connection key
 * @returns
 */
export const formatKey = (key: string): string =>
  key.toLowerCase().replace(/ |\./g, "_");

/**
 * Modify the current history entry, replacing it with the new URL
 * @param key Connection key
 * @param url URL of the history entry
 */
export const replaceURL = (key: string, url: string): void => {
  const destination = `${window.location.origin + url}&key=${key}`;
  if (window.location.href.toLowerCase() !== destination.toLowerCase()) {
    window.history.replaceState(null, "", destination);
  }
};
