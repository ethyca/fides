import { useEffect, useState } from "preact/hooks";

import { searchForElement } from "../ui-utils";

/**
 * Hook that searches for a DOM element by ID and returns it when found
 * @param elementId - The ID of the element to find
 * @param isDisabled - Optional flag to disable the hook
 * @returns The found element or null if not found
 */
const useElementById = <T extends HTMLElement = HTMLElement>(
  elementId: string,
  isDisabled?: boolean,
): T | null => {
  const [element, setElement] = useState<T | null>(null);

  // eslint-disable-next-line consistent-return
  useEffect(() => {
    if (isDisabled) {
      return () => {};
    }
    searchForElement(elementId).then((foundElement) => {
      setElement(foundElement as T);
    });
  }, [elementId, isDisabled]); // Only re-run if ID changes

  return element;
};

export default useElementById;
