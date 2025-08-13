import { createContext } from "preact";
import { ReactNode } from "preact/compat";
import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "preact/hooks";

interface LiveRegionContextValue {
  message: string;
  announce: (message: string) => void;
  clear: () => void;
}

const LiveRegionContext = createContext<LiveRegionContextValue | undefined>(
  undefined,
);

/**
 * A provider that provides the live region context.
 * Listens for Fides events and announces the message to the screen reader.
 */
export const LiveRegionProvider = ({ children }: { children: ReactNode }) => {
  const [message, setMessage] = useState<string>("");

  const announce = useCallback((newMessage: string) => {
    // Clear first to retrigger screen reader announcement when message repeats
    setMessage("");
    // Defer to next tick to ensure DOM mutation
    setTimeout(() => {
      setMessage(newMessage);
    }, 0);
  }, []);

  const clear = useCallback(() => {
    setMessage("");
  }, []);

  const value = useMemo(
    () => ({ message, announce, clear }),
    [message, announce, clear],
  );

  useEffect(() => {
    const handleAnnounce = () => {
      announce("Preferences updated");
    };
    const handleClear = () => {
      clear();
    };
    window.addEventListener("FidesUIShown", handleClear);
    window.addEventListener("FidesUpdated", handleAnnounce);
    return () => {
      window.removeEventListener("FidesUIShown", handleClear);
      window.removeEventListener("FidesUpdated", handleAnnounce);
    };
  }, [announce, clear]);

  return (
    <LiveRegionContext.Provider value={value}>
      {children}
    </LiveRegionContext.Provider>
  );
};

/**
 * A hook that provides the live region context.
 * Use in conjunction with the `LiveRegion` component to announce messages.
 * Preferences are already handled by the listeners above. Any other messages
 * should be announced using this hook.
 *
 * @example
 * ```tsx
 * const { announce } = useLiveRegion();
 * announce("Something happened");
 * ```
 */
export const useLiveRegion = () => {
  const context = useContext(LiveRegionContext);
  if (!context) {
    throw new Error("useLiveRegion must be used within a LiveRegionProvider");
  }
  return context;
};
