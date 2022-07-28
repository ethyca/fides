import { LegacyRef, useEffect, useRef } from "react";

// eslint-disable-next-line import/prefer-default-export
export const useOutsideClick = (handleClick: () => void) => {
  const ref = useRef<HTMLDivElement | undefined>(undefined) as
    | LegacyRef<HTMLDivElement>
    | undefined;
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      // @ts-ignore
      if (!ref.current?.contains(event.target)) {
        handleClick();
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [ref, handleClick]);

  return { ref };
};
