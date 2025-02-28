import { GppModel } from "@iabgpp/cmpapi";

import { fidesSupportedGPPApis } from "./constants";

/**
 * Represents a decoded section from a GPP string.
 * Each section corresponds to a specific privacy framework or region's requirements.
 */
export interface DecodedGppSection {
  id: number;
  name: string;
  data: Record<string, unknown>;
}

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
export function decodeGppString(gppString: string): DecodedGppSection[] {
  if (!gppString) {
    throw new Error("GPP string cannot be empty");
  }

  try {
    // Create a new GPP model instance to decode the string
    const gppModel = new GppModel(gppString);

    // Get section IDs from the header
    const sectionIds = gppModel.getSectionIds();

    // Decode each section
    const sections = sectionIds.map((sectionId) => {
      // Find the section name from our mapping or use section ID
      const sectionName = fidesSupportedGPPApis.find(
        (api) => api.ID === sectionId,
      )?.NAME;
      if (!sectionName || !hasGppSection(gppString, sectionName)) {
        return undefined;
      }
      const sectionData = gppModel.getSection(sectionName) ?? {};

      const decodedSection: DecodedGppSection = {
        id: sectionId,
        name: sectionName,
        data: sectionData,
      };
      return decodedSection;
    });

    return sections.filter(
      (section): section is DecodedGppSection => section !== undefined,
    );
  } catch (error) {
    throw new Error(
      `Failed to decode GPP string: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
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
