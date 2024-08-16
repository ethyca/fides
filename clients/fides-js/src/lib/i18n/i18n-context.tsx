import { createContext, FunctionComponent, h } from "preact";
import {
  Dispatch,
  StateUpdater,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "preact/hooks";

import { FIDES_I18N_ICON } from "../consent-constants";

interface I18nContextProps {
  currentLocale: string | undefined;
  setCurrentLocale: Dispatch<StateUpdater<string | undefined>>;
  isLoading: boolean;
  setIsLoading: Dispatch<StateUpdater<boolean>>;
}

const I18nContext = createContext<I18nContextProps | Record<any, never>>({});

export const I18nProvider: FunctionComponent = ({ children }) => {
  const [currentLocale, setCurrentLocale] = useState<string>();
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    const icon = document.getElementById(FIDES_I18N_ICON);
    if (isLoading) {
      icon?.style.setProperty("animation-name", "spin");
    } else {
      icon?.style.removeProperty("animation-name");
    }
  }, [isLoading]);

  const value: I18nContextProps = useMemo(
    () => ({ currentLocale, setCurrentLocale, isLoading, setIsLoading }),
    [currentLocale, isLoading],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error("useI18n must be used within a I18nProvider");
  }
  return context;
};
