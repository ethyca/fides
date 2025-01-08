import { ConsentMethod, FidesInitOptions } from "./consent-types";

export const raise = (message: string) => {
  throw new Error(message);
};

/**
 * Extracts the id value of each object in the list and returns a list
 * of IDs, either strings or numbers based on the IDs' type.
 */
export const extractIds = <T extends { id: string | number }[]>(
  modelList?: T,
): any[] => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => model.id);
};

export const isConsentOverride = (options: FidesInitOptions) => {
  return (
    options.fidesConsentOverride === ConsentMethod.ACCEPT ||
    options.fidesConsentOverride === ConsentMethod.REJECT
  );
};
