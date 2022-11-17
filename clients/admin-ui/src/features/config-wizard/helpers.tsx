import { Dataset, System } from "~/types/api";

export const isSystem = (sd: System | Dataset): sd is System =>
  "system_type" in sd;
