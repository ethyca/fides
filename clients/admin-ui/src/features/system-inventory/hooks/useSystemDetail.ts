import { MOCK_SYSTEMS } from "../mock-data";
import type { MockSystem } from "../types";

export const useSystemDetail = (
  id: string | undefined,
): MockSystem | null => {
  if (!id) return null;
  return MOCK_SYSTEMS.find((s) => s.fides_key === id) ?? null;
};
