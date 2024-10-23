import { useEffect, useState } from "preact/hooks";

/**
 * This React hook listens for matches to a CSS media query. It allows the rendering of components based on whether the query matches or not. The media query string can be any valid CSS media query, for example '(prefers-color-scheme: dark)'.
 * @param query - The CSS media query string to match against the viewport.
 * @example const isMobile = useMediaQuery('(max-width: 768px)');
 * @returns A boolean value indicating whether the media query matches the current viewport.
 */
export const useMediaQuery = (query: string) => {
  const [matches, setMatches] = useState<boolean>(false);
  useEffect(() => {
    const matchQueryList = window.matchMedia(query);
    setMatches(matchQueryList.matches);
    function handleChange(e: MediaQueryListEvent) {
      setMatches(e.matches);
    }

    if (matchQueryList.addEventListener) {
      matchQueryList.addEventListener("change", handleChange);
    } else {
      // Supports Safari < 14
      matchQueryList.addListener(handleChange);
    }
    return () => {
      if (matchQueryList.removeEventListener) {
        matchQueryList.removeEventListener("change", handleChange);
      } else {
        // Supports Safari < 14
        matchQueryList.removeListener(handleChange);
      }
    };
  }, [query]);
  return matches;
};
