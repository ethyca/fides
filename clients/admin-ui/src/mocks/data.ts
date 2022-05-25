import { System } from "~/features/system/types";

/**
 * Returns a mock system object. Can override default values by
 * passing in a Partial<System>
 */
export const mockSystem = (partialSystem?: Partial<System>): System => {
  const system: System = {
    system_type: "Service",
    data_responsibility_title: "Controller",
    privacy_declarations: [],
    data_protection_impact_assessment: { is_required: true },
    fides_key: "analytics_system",
    organization_fides_key: "sample_organization",
  };
  return Object.assign(system, partialSystem);
};

/**
 * Returns a list of mock systems of length `number`
 */
export const mockSystems = (number: number) =>
  Array.from({ length: number }, (_, i) =>
    mockSystem({
      system_type: `Service ${i}`,
      fides_key: `analytics_system_${i}`,
    })
  );
