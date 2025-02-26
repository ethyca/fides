import { createContext, h } from "preact";
import { ReactNode, useContext, useMemo, useState } from "preact/compat";

import { GVLTranslationJson } from "./types";

interface GVLContextProps {
  gvlTranslations: GVLTranslationJson | undefined;
  setGvlTranslations: (t: GVLTranslationJson) => void;
}
export const GVLContext = createContext<GVLContextProps | Record<any, never>>(
  {},
);

interface GVLProviderProps {
  children: ReactNode;
}
export const GVLProvider = ({ children }: GVLProviderProps) => {
  const [gvlTranslations, setGvlTranslations] = useState<GVLTranslationJson>();

  const value: GVLContextProps = useMemo(
    () => ({
      gvlTranslations,
      setGvlTranslations,
    }),
    [gvlTranslations, setGvlTranslations],
  );
  return <GVLContext.Provider value={value}>{children}</GVLContext.Provider>;
};

export const useGvl = () => {
  const context = useContext(GVLContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error("useGvl must be used within a GVLProvider");
  }
  return context;
};
