import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { useCallback, useMemo } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { type RootState } from "~/app/store";
import { selectInitialConnections } from "~/features/datastore-connections";
import { selectHealth } from "~/features/plus/plus.slice";
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
};

const initialState: FeaturesState = { flags: {} };

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
      const flagEnv = draftState.flags[payload.flag] ?? {
        ...FLAG_CONFIG[payload.flag],
      };

      flagEnv[payload.env ?? "development"] = payload.value;

      draftState.flags[payload.flag] = flagEnv;
    },
    reset(draftState) {
      draftState.flags = {};
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
  plus: boolean;
  systemsCount: number;
  connectionsCount: number;
  dataFlowScanning: boolean;

  flags: FlagsFor<FlagConfig>;
};

export const useFeatures = (): Features => {
  const health = useAppSelector(selectHealth);
  const allSystems = useAppSelector(selectAllSystems);
  const initialConnections = useAppSelector(selectInitialConnections);

  const plus = health !== undefined;
  const dataFlowScanning = health ? !!health.system_scanner.enabled : false;

  const systemsCount = allSystems?.length ?? 0;

  const connectionsCount = initialConnections?.total ?? 0;

  const { flags } = useFlags();

  return {
    plus,
    systemsCount,
    connectionsCount,
    dataFlowScanning,
    flags,
  };
};
