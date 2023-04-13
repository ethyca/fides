import { ScopeRegistryEnum } from "~/types/api";

import { ModuleCardConfig } from "./types";

export const configureTiles = ({
  config,
  userScopes,
  hasPlus = false,
}: {
  config: ModuleCardConfig[];
  userScopes: ScopeRegistryEnum[];
  hasPlus?: boolean;
  hasSystems?: boolean;
  hasConnections?: boolean;
}): ModuleCardConfig[] => {
  let filteredConfig = config;

  if (!hasPlus) {
    filteredConfig = filteredConfig.filter((c) => !c.requiresPlus);
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
  return filteredByScope;
};
