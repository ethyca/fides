import { FlagNames } from "~/features/common/features";
import { ScopeRegistryEnum } from "~/types/api";

type ModuleCard = {
  description: string;
  href: string;
  key: number;
  name: string;
  sortOrder: number;
  title: string;
  color: string;
};

export interface ModuleCardConfig extends ModuleCard {
  requiresSystems?: boolean;
  requiresConnections?: boolean;
  requiresPlus?: boolean;
  requiresOss?: boolean;
  scopes: ScopeRegistryEnum[];
  requiresFlag?: FlagNames;
}
