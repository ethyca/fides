import { createContext, useContext, useMemo, useState } from "react";
import { I18n, setupI18n } from "fides-js";

interface I18nContextProps {
  currentLocale: string | undefined;
  setCurrentLocale: (newLocale: string) => void;
  i18nInstance: I18n;
  setI18nInstance: (newI18n: I18n) => void;
}

const I18nContext = createContext<I18nContextProps>({} as I18nContextProps);

export const I18nProvider: React.FC = ({ children }) => {
  const [currentLocale, setCurrentLocale] = useState<string>();
  const [i18nInstance, setI18nInstance] = useState<I18n>(setupI18n());

  const value: I18nContextProps = useMemo(
    () => ({ currentLocale, setCurrentLocale, i18nInstance, setI18nInstance }),
    [currentLocale, i18nInstance]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = () => {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used within a I18nProvider");
  }
  return { ...context, i18n: context.i18nInstance };
};
