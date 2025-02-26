import { GppModel } from "@iabgpp/cmpapi";

import { FIDES_REGION_TO_GPP_SECTION } from "./constants";
import { GPPSection } from "./types";

/**
 * Represents a decoded section from a GPP string.
 * Each section corresponds to a specific privacy framework or region's requirements.
 */
export interface DecodedGppSection {
  /**
   * The numeric identifier of the section as defined in the GPP specification.
   * For example:
   * - 6: USP v1.0 (CCPA)
   * - 7: US National
   * - 8: US State-specific
   */
  id: number;

  /**
   * The human-readable name of the section, mapped from the section ID using FIDES_REGION_TO_GPP_SECTION.
   * If no mapping exists, falls back to `section_${id}`.
   * Common values include:
   * - "uspv1": US Privacy (CCPA)
   * - "usnat": US National
   * - "usca": California
   * - "usva": Virginia
   */
  name: string;

  /**
   * The decoded data for this section, as returned by GppModel.getSection().
   * The structure varies by section type. Common fields include:
   *
   * For uspv1 (id: 6):
   * {
   *   Version: number;
   *   Notice: number;
   *   OptOutSale: number;
   *   LspaCovered: number;
   * }
   *
   * For usnat (id: 7):
   * {
   *   SharingNotice: number;
   *   SaleOptOutNotice: number;
   *   SharingOptOutNotice: number;
   *   TargetedAdvertisingOptOutNotice: number;
   *   SensitiveDataProcessingOptOutNotice: number;
   *   ...
   * }
   */
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
export interface DecodedGpp {
  /**
   * The GPP header information, containing metadata about the included sections.
   * This data comes from GppModel.getHeader() and GppModel.getSectionIds().
   */
  header: {
    /**
     * Array of section IDs present in the GPP string.
     * The order matches the order of sections in the encoded string.
     */
    sectionIds: number[];
  };

  /**
   * Array of decoded sections from the GPP string.
   * Each section is decoded using GppModel.getSection() and transformed
   * into a strongly-typed DecodedGppSection object.
   *
   * Sections are processed in the order they appear in the GPP string.
   * If a section cannot be decoded, an error is thrown rather than
   * producing partial or invalid data.
   *
   * @see DecodedGppSection for details about section structure
   */
  sections: DecodedGppSection[];
}

/**
 * Decodes a GPP string into its component sections and values.
 * Uses the IAB GPP CMP API for decoding to ensure compliance with the specification.
 *
 * @param gppString - The GPP string to decode
 * @returns DecodedGpp object containing header and decoded sections
 * @throws Error if the GPP string is invalid or empty
 */
export function decodeGppString(gppString: string): DecodedGpp {
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
      const section = Object.values(FIDES_REGION_TO_GPP_SECTION).find(
        (s: GPPSection) => s.id === sectionId,
      );

      const name = section?.name ?? `section_${sectionId}`;
      const sectionData = gppModel.getSection(name) ?? {};

      // For TCF EU v2, we need to use the numeric section ID
      if (sectionId === 2) {
        return {
          id: sectionId,
          name: "section_2",
          data: gppModel.getSection("2") ?? {},
        };
      }

      return {
        id: sectionId,
        name,
        data: sectionData,
      };
    });

    return {
      header: {
        sectionIds,
      },
      sections,
    };
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

    // For TCF EU v2, we need to use the numeric section ID
    const actualSectionName = sectionName === "section_2" ? "2" : sectionName;

    if (!gppModel.hasSection(actualSectionName)) {
      return null;
    }
    return gppModel.getFieldValue(actualSectionName, fieldName);
  } catch {
    return null;
  }
}

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

    // For TCF EU v2, we need to use the numeric section ID
    const actualSectionName = sectionName === "section_2" ? "2" : sectionName;

    return gppModel.hasSection(actualSectionName);
  } catch {
    return false;
  }
}
