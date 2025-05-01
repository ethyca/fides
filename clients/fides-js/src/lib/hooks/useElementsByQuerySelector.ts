import { useEffect, useState } from "preact/hooks";

import { searchForElementsByQuerySelector } from "../ui-utils";

/**
 * Hook that searches for DOM elements by class and returns them when found
 * @param className - The ID of the element to find
 * @param isDisabled - Optional flag to disable the hook
 * @returns The found element or null if not found
 */
const useElementByQuerySelector = <T extends HTMLElement = HTMLElement>(
  className: string,
  isDisabled?: boolean,
): Array<T> => {
  const [elements, setElements] = useState<Array<T>>([]);

  // eslint-disable-next-line consistent-return
  useEffect(() => {
    if (isDisabled) {
      return () => {};
    }
    searchForElementsByQuerySelector(className).then((foundElements) => {
      setElements(Array.from(foundElements) as T[]);
    });
  }, [className, isDisabled]); // Only re-run if ID changes

  return elements;
};

export default useElementByQuerySelector;
