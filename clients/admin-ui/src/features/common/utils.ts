import { format } from "date-fns-tz";

export const capitalize = (text: string): string =>
  text.replace(/^\w/, (c) => c.toUpperCase());

/**
 * "Fun On A Bun" => "Fun on a bun"
 * "fun on a bun" => "Fun on a bun"
 */
export const sentenceCase = (text: string) => {
  const lower = text.toLocaleLowerCase();
  const init = lower.substring(0, 1);
  const rest = lower.substring(1);
  return `${init.toLocaleUpperCase()}${rest}`;
};

/**
 * "funOnABun" => "Fun on a bun"
 */
export const camelToSentenceCase = (text: string) => {
  const withSpaces = text.replaceAll(/([a-z])([A-Z])/g, "$1 $2");
  return sentenceCase(withSpaces);
};

export const debounce = (fn: (props?: any) => void, ms = 0) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  // eslint-disable-next-line func-names
  return function (this: any, ...args: any[]) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply<any, any[], void>(this, args), ms);
  };
};

export const formatDate = (value: string | number | Date): string =>
  format(new Date(value), "MMMM d, y, KK:mm:ss z");

export const utf8ToB64 = (str: string): string =>
  window.btoa(unescape(encodeURIComponent(str)));

export const getFileNameFromContentDisposition = (
  contentDisposition: string | null,
) => {
  const defaultName = "export";
  if (!contentDisposition) {
    return defaultName;
  }
  const match = contentDisposition.match(/filename=(.+)/);
  return match ? match[1] : defaultName;
};

/**
 * Constructs a query string from an array of values.
 *
 * @param valueList - An array of string values to be included in the query string.
 * @param queryParam - The name of the query parameter.
 * @returns A query string where each value from the array is assigned to the query parameter.
 * If the array is empty, the function returns undefined.
 *
 * @example
 * getQueryParamsFromArray(['1', '2', '3'], 'id');
 * // returns 'id=1&id=2&id=3'
 */
export const getQueryParamsFromArray = (
  valueList: string[],
  queryParam: string,
) => {
  if (valueList.length > 0) {
    return `${queryParam}=${valueList.join(`&${queryParam}=`)}`;
  }
  return undefined;
};

/**
 * Masks sensitive data with asterisks unless specified to reveal it.
 * @param {string} sensitiveData - The `sensitiveData` parameter is a string that contains potentially sensitive Personally Identifiable Information (PII) such as names, addresses, phone numbers, or email addresses.
 * @param {boolean} [revealPII=false] - The `revealPII` parameter is a boolean flag that determines whether PII should be revealed or masked.
 * @returns returns the original `data` string with all characters replaced by "*" if `revealPII` is set to `false`. If `revealPII` is set to `true`, then the original `sensitiveData` string is returned as is.
 */
export const getPII = (sensitiveData: string, revealPII: boolean = false) => {
  const pii = revealPII ? sensitiveData : sensitiveData.replace(/./g, "*");
  return pii;
};

/**
 * Creates a new Map with boolean values based on selections made based on original Map.
 * @param originalMap - The `originalMap` parameter is a Map object that contains the original key-value pairs.
 * @param selectedKeys - The `selectedKeys` parameter is an array of strings that contains the keys of the selected items.
 * @returns a new Map object with the same keys as the `originalMap` parameter, but with boolean values that indicate whether the key is selected or not.
 */
export const createSelectedMap = <T = string>(
  originalMap: Map<T, string>,
  selectedKeys: T[] | undefined,
): Map<string, boolean> => {
  const selectedMap = new Map<string, boolean>();
  originalMap.forEach((value, key) => {
    selectedMap.set(value, !!selectedKeys?.includes(key));
  });
  return selectedMap;
};

/**
 * gets a list of keys from a map where the value matches an array of values
 */
export const getKeysFromMap = <T = string>(
  map: Map<T, unknown>,
  values: unknown[] | undefined,
): T[] =>
  Array.from(map)
    .filter(([, value]) => values?.includes(value))
    .map(([key]) => key);

export const getOptionsFromMap = <T = string>(
  map: Map<T, string>,
): { label: string; value: T }[] =>
  Array.from(map).map(([key, value]) => ({
    label: value,
    value: key,
  }));

export const getWebsiteIconUrl = (hostname: string) => {
  return `https://icons.duckduckgo.com/ip3/${hostname}.ico`;
};
