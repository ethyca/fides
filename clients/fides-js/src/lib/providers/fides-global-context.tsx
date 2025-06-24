import { createContext, h } from "preact";
import { ReactNode } from "preact/compat";
import { useContext, useMemo, useState } from "preact/hooks";

import {
  FidesConfig,
  FidesCookie,
  FidesGlobal,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../consent-types";

/**
 * This is the same as the FidesGlobal type, but with the
 * cookie, config, experience, and fidesRegionString properties
 * populated and not undefined or empty since those have all been
 * populated and validated by the initialize function. This can
 * confidently be used by the Preact app.
 */
export interface InitializedFidesGlobal extends FidesGlobal {
  cookie: FidesCookie;
  config: FidesConfig;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  fidesRegionString: string;
}

interface UseFidesGlobalProps {
  fidesGlobal: InitializedFidesGlobal;
  setFidesGlobal: (fidesGlobal: InitializedFidesGlobal) => void;
}

const FidesGlobalContext = createContext<
  UseFidesGlobalProps | Record<any, never>
>({});

export const FidesGlobalProvider = ({
  initializedFides,
  children,
}: {
  initializedFides: InitializedFidesGlobal;
  children: ReactNode;
}) => {
  const [fidesGlobal, setFidesGlobal] =
    useState<InitializedFidesGlobal>(initializedFides);

  const value: UseFidesGlobalProps = useMemo(
    () => ({
      fidesGlobal,
      setFidesGlobal,
    }),
    [fidesGlobal, setFidesGlobal],
  );
  return (
    <FidesGlobalContext.Provider value={value}>
      {children}
    </FidesGlobalContext.Provider>
  );
};

export const useFidesGlobal = () => {
  const context = useContext(FidesGlobalContext);
  if (!context || Object.keys(context).length === 0) {
    throw new Error("useFidesGlobal must be used within a FidesGlobalProvider");
  }
  return context as UseFidesGlobalProps;
};
