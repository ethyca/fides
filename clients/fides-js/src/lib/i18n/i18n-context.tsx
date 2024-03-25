import { createContext, h, FunctionComponent } from "preact";
import { useContext, useState, useMemo, StateUpdater } from "preact/hooks";
import { i18n } from "./index";

interface I18nContextProps {
  currentLocale: string;
  setCurrentLocale: StateUpdater<string>;
}

const I18nContext = createContext<I18nContextProps>({} as I18nContextProps);

export const I18nProvider: FunctionComponent = ({ children }) => {
  const { locale } = i18n;
  const [currentLocale, setCurrentLocale] = useState(locale);

  const value: I18nContextProps = useMemo(
    () => ({ currentLocale, setCurrentLocale }),
    [currentLocale]
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
