import { ScopeRegistryEnum } from "~/types/api";

import { ModuleCardConfig } from "./types";

export const configureTiles = ({
  config,
  userScopes,
  hasPlus = false,
  flags,
}: {
  config: ModuleCardConfig[];
  userScopes: ScopeRegistryEnum[];
  hasPlus?: boolean;
  hasSystems?: boolean;
  hasConnections?: boolean;
  flags: Record<string, boolean>;
}): ModuleCardConfig[] => {
  let filteredConfig = config;

  if (!hasPlus) {
    filteredConfig = filteredConfig.filter((c) => !c.requiresPlus);
  } else {
    filteredConfig = filteredConfig.filter((c) => !c.requiresOss);
  }

  const filteredByScope: ModuleCardConfig[] = [];
  filteredConfig.forEach((moduleConfig) => {
    if (moduleConfig.scopes.length === 0) {
      filteredByScope.push(moduleConfig);
    } else if (
      moduleConfig.scopes.filter((scope) => userScopes.includes(scope)).length >
      0
    ) {
      filteredByScope.push(moduleConfig);
    }
  });

  const filteredByFlag: ModuleCardConfig[] = [];
  filteredByScope.forEach((moduleConfig) => {
    if (!moduleConfig.requiresFlag) {
      filteredByFlag.push(moduleConfig);
    } else if (flags[moduleConfig.requiresFlag]) {
      filteredByFlag.push(moduleConfig);
    }
  });
  return filteredByFlag;
};
