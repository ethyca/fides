import { I18n, setupI18n } from "fides-js";
import { createContext, ReactNode, useMemo, useState } from "react";

interface I18nContextProps {
  currentLocale: string | undefined;
  setCurrentLocale: (newLocale: string) => void;
  i18nInstance: I18n;
  setI18nInstance: (newI18n: I18n) => void;
}

export const I18nContext = createContext<I18nContextProps>(
  {} as I18nContextProps,
);

export const I18nProvider = ({ children }: { children: ReactNode }) => {
  const [currentLocale, setCurrentLocale] = useState<string>();
  const [i18nInstance, setI18nInstance] = useState<I18n>(setupI18n());

  const value: I18nContextProps = useMemo(
    () => ({ currentLocale, setCurrentLocale, i18nInstance, setI18nInstance }),
    [currentLocale, i18nInstance],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};
