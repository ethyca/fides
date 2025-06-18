import { useEffect, useRef } from "react";

/**
 * Hook that triggers a callback when clicking outside of the referenced element
 * @param callback - Function to call when clicking outside
 * @returns ref to attach to the element you want to detect clicks outside of
 */
const useClickOutside = <T extends HTMLElement = HTMLElement>(
  callback: () => void,
) => {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [callback]);

  return ref;
};

export default useClickOutside;
