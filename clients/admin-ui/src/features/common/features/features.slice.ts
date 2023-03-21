import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useCallback, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { type RootState } from "~/app/store";
import { selectHealth } from "~/features/common/health.slice";
import { selectInitialConnections } from "~/features/datastore-connections";
import { selectHealth as selectPlusHealth } from "~/features/plus/plus.slice";
import { selectAllSystems } from "~/features/system";
import flagDefaults from "~/flags.json";

import { configureFlags, flagsForEnv } from "./config";
import { Env, FlagsFor, NamesFor, ValueFor } from "./types";

export const FLAG_CONFIG = configureFlags(flagDefaults);
export type FlagConfig = typeof FLAG_CONFIG;
export const FLAG_NAMES = Object.keys(FLAG_CONFIG) as Array<
  NamesFor<FlagConfig>
>;

type FeaturesState = {
  flags: Partial<FlagConfig>;
  showNotificationBanner: boolean;
};

const initialState: FeaturesState = { flags: {}, showNotificationBanner: true };

const featuresSlice = createSlice({
  name: "features",
  initialState,
  reducers: {
    override<FN extends NamesFor<FlagConfig>>(
      draftState: FeaturesState,
      {
        payload,
      }: PayloadAction<{
        flag: FN;
        env?: Env;
        value: ValueFor<FlagConfig, FN>;
      }>
    ) {
      const { development, test, production } =
        draftState.flags[payload.flag] ?? FLAG_CONFIG[payload.flag];

      const flagEnv = {
        development,
        test,
        production,
      };
      flagEnv[payload.env ?? "development"] = payload.value;

      draftState.flags[payload.flag] = flagEnv;
    },
    reset(draftState) {
      draftState.flags = {};
    },
    setShowNotificationBanner(draftState, action: PayloadAction<boolean>) {
      draftState.showNotificationBanner = action.payload;
    },
  },
});

export const { reducer } = featuresSlice;

export const selectFeatures = (state: RootState) => state.features;
export const selectFlags = createSelector(
  selectFeatures,
  (state) => state.flags
);
export const selectEnvFlags = createSelector(
  selectFlags,
  (flags): FlagsFor<FlagConfig> =>
    flagsForEnv({ ...FLAG_CONFIG, ...flags }, process.env.NEXT_PUBLIC_APP_ENV)
);

/**
 * Notification banner specific. If we one day end up with more notification
 * related logic, we should move this to its own slice.
 */
export const selectShowNotificationBanner = createSelector(
  selectFeatures,
  (state) => state.showNotificationBanner
);

export const { setShowNotificationBanner } = featuresSlice.actions;

export const useFlags = () => {
  const dispatch = useAppDispatch();
  const flags = useAppSelector(selectEnvFlags);

  const defaults = useMemo(
    () => flagsForEnv(FLAG_CONFIG, process.env.NEXT_PUBLIC_APP_ENV),
    []
  );

  const override = useCallback(
    <FN extends NamesFor<FlagConfig>>({
      flag,
      value,
    }: {
      flag: FN;
      value: ValueFor<FlagConfig, FN>;
    }) => {
      dispatch(
        featuresSlice.actions.override({
          flag,
          env: process.env.NEXT_PUBLIC_APP_ENV,
          value,
        })
      );
    },
    [dispatch]
  );

  const reset = useCallback(() => {
    dispatch(featuresSlice.actions.reset());
  }, [dispatch]);

  return {
    flags,
    defaults,
    reset,
    override,
  };
};

export type Features = {
  version: string | undefined;
  plus: boolean;
  systemsCount: number;
  connectionsCount: number;
  dataFlowScanning: boolean;

  flags: FlagsFor<FlagConfig>;
};

export const useFeatures = (): Features => {
  const health = useAppSelector(selectHealth);
  const plusHealth = useAppSelector(selectPlusHealth);
  const allSystems = useAppSelector(selectAllSystems);
  const initialConnections = useAppSelector(selectInitialConnections);

  const version = health?.version;

  const plus = plusHealth !== undefined;
  const dataFlowScanning = plusHealth
    ? !!plusHealth.system_scanner.enabled
    : false;

  const systemsCount = allSystems?.length ?? 0;

  const connectionsCount = initialConnections?.total ?? 0;

  const { flags } = useFlags();

  return {
    version,
    plus,
    systemsCount,
    connectionsCount,
    dataFlowScanning,
    flags,
  };
};
