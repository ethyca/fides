import { CmpApi, GppModel } from "@iabgpp/cmpapi";

import { ETHYCA_CMP_ID } from "../tcf/constants";
import { CMP_VERSION } from "./constants";

/**
 * Represents a fully decoded GPP (Global Privacy Platform) string.
 * This interface provides a strongly-typed structure for working with GPP data
 * that has been decoded using the IAB's GppModel class.
 *
 * Example GPP string: "DBAA~BOS9A" decodes to:
 * {
 *   header: {
 *     sectionIds: [6]
 *   },
 *   sections: [{
 *     id: 6,
 *     name: "uspv1",
 *     data: {
 *       Version: 1,
 *       Notice: 2,
 *       OptOutSale: 1,
 *       LspaCovered: 1
 *     }
 *   }]
 * }
 */

/**
 * Checks if a GPP string contains a specific section.
 *
 * @param gppString - The GPP string to check
 * @param sectionName - The name of the section to look for
 * @returns true if the section exists, false otherwise
 */
export function hasGppSection(gppString: string, sectionName: string): boolean {
  try {
    const gppModel = new GppModel(gppString);
    return gppModel.hasSection(sectionName);
  } catch {
    return false;
  }
}

/**
 * Decodes a GPP string into its component sections and values.
 * Uses the IAB GPP CMP API for decoding to ensure compliance with the specification.
 *
 * @param gppString - The GPP string to decode
 * @returns DecodedGpp object containing header and decoded sections
 * @throws Error if the GPP string is invalid or empty
 */
export function decodeGppString(
  gppString: string,
): Array<{ id: number; name: string; data: unknown }> {
  if (!gppString) {
    throw new Error("GPP string cannot be empty");
  }
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION);
  cmpApi.setGppString(gppString);
  const sections = cmpApi.getObject();
  if (!sections) {
    throw new Error("Failed to decode GPP string");
  }

  // Map section IDs to their names
  const sectionIdMap: Record<string, number> = {
    tcfeuv2: 2,
    usnat: 7,
    usca: 8,
  };

  // Transform the object into an array of sections
  return Object.entries(sections).map(([name, data]) => ({
    id: sectionIdMap[name] || 0,
    name,
    data,
  }));
}

/**
 * Gets the value of a specific field from a GPP section.
 *
 * @param gppString - The GPP string to get the field from
 * @param sectionName - The name of the section (e.g., "uspv1", "usnat")
 * @param fieldName - The name of the field within the section
 * @returns The field value if found, null otherwise
 */
export function getGppField(
  gppString: string,
  sectionName: string,
  fieldName: string,
): unknown {
  try {
    const gppModel = new GppModel(gppString);
    if (!gppModel.hasSection(sectionName)) {
      return null;
    }
    return gppModel.getFieldValue(sectionName, fieldName);
  } catch {
    return null;
  }
}
