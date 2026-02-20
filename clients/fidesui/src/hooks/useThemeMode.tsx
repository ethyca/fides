import {
  createContext,
  CSSProperties,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

export type ThemeMode = "light" | "dark";

interface ThemeModeContextValue {
  mode: ThemeMode;
  resolvedMode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

const STORAGE_KEY = "fides-theme-mode";

const ThemeModeContext = createContext<ThemeModeContextValue | undefined>(
  undefined,
);

function getStoredMode(): ThemeMode | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") {
      return stored;
    }
  } catch {
    // Swallow storage errors (e.g. disabled storage, privacy mode, quota issues)
  }
  return undefined;
}

export interface ThemeModeProviderProps {
  children: ReactNode;
  defaultMode?: ThemeMode;
  attribute?: string;
  wrapperStyle?: CSSProperties;
  locked?: boolean;
}

export const ThemeModeProvider = ({
  children,
  defaultMode = "light",
  attribute = "data-theme",
  wrapperStyle = { height: "100%" },
  locked = false,
}: ThemeModeProviderProps) => {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (locked) {
      return defaultMode;
    }
    return getStoredMode() ?? defaultMode;
  });

  const setMode = useCallback(
    (newMode: ThemeMode) => {
      if (locked) {
        return;
      }
      setModeState(newMode);
      if (typeof window === "undefined") {
        return;
      }
      try {
        localStorage.setItem(STORAGE_KEY, newMode);
      } catch {
        // Swallow storage errors to avoid crashing the app
      }
    },
    [locked],
  );

  useEffect(() => {
    if (locked) {
      setModeState(defaultMode);
    }
  }, [locked, defaultMode]);

  const effectiveMode: ThemeMode = locked ? defaultMode : mode;

  const value = useMemo(
    () => ({
      mode: effectiveMode,
      resolvedMode: effectiveMode,
      setMode,
    }),
    [effectiveMode, setMode],
  );

  const contextProvider = (
    <ThemeModeContext.Provider value={value}>
      {children}
    </ThemeModeContext.Provider>
  );

  return (
    <div
      {...{ [attribute]: effectiveMode }}
      style={wrapperStyle}
    >
      {contextProvider}
    </div>
  );
};

export const useThemeMode = (): ThemeModeContextValue => {
  const context = useContext(ThemeModeContext);
  if (!context) {
    throw new Error("useThemeMode must be used within a ThemeModeProvider");
  }
  return context;
};
