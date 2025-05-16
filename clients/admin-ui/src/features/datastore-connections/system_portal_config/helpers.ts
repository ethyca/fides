/**
 * Format the Connection key to be lower case and replace empty spaces with an underscore
 * @param key Connection key
 * @returns
 */
export const formatKey = (key: string): string =>
  key
    .toLowerCase()
    .replace(/[ .]/g, "_") // replace spaces and dots with underscores
    .replace(/[^a-zA-Z0-9_<>-]/g, ""); // only allow alphanumeric characters or select special characters

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
