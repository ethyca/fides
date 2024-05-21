/**
 * Extracts the path from a raw URL by removing any query parameters or fragments.
 *
 * @param rawUrl - The raw URL string.
 * @returns The path extracted from the raw URL.
 */
const getPathFromRawUrl = (rawUrl: string) => rawUrl.split(/[?#]/)[0];

export default getPathFromRawUrl;
