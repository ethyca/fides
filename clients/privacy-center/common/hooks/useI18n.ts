import { useContext } from "react";
import { I18nContext } from "../i18nContext";

const useI18n = () => {
  const context = useContext(I18nContext);
  const i18n = context.i18nInstance;

  if (!context) {
    throw new Error("useI18n must be used within a I18nProvider");
  }

  return { ...context, i18n };
};
export default useI18n;
