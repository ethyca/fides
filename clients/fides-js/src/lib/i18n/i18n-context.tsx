import { createContext, FunctionComponent, h } from "preact";
import {
  Dispatch,
  StateUpdater,
  useContext,
  useMemo,
  useState,
} from "preact/hooks";

interface I18nContextProps {
  currentLocale: string | undefined;
  setCurrentLocale: Dispatch<StateUpdater<string | undefined>>;
}

const I18nContext = createContext<I18nContextProps>({} as I18nContextProps);

export const I18nProvider: FunctionComponent = ({ children }) => {
  const [currentLocale, setCurrentLocale] = useState<string>();

  const value: I18nContextProps = useMemo(
    () => ({ currentLocale, setCurrentLocale }),
    [currentLocale],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within a I18nProvider");
  }
  return context;
};
