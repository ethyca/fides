import { ScopeRegistry } from "~/types/api";

import { ModuleCardConfig } from "./types";

export const configureTiles = ({
  config,
  userScopes,
  hasPlus = false,
  hasSystems = false,
  hasConnections = false,
}: {
  config: ModuleCardConfig[];
  userScopes: ScopeRegistry[];
  hasPlus?: boolean;
  hasSystems?: boolean;
  hasConnections?: boolean;
}): ModuleCardConfig[] => {
  let filteredConfig = config;

  if (!hasPlus) {
    filteredConfig = filteredConfig.filter((c) => !c.requiresPlus);
  }

  if (!hasSystems) {
    filteredConfig = filteredConfig.filter((c) => !c.requiresSystems);
  }

  if (!hasConnections) {
    filteredConfig = filteredConfig.filter((c) => !c.requiresConnections);
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
