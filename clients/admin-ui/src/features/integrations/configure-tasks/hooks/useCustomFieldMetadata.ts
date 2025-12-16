import { useMemo } from "react";

import { extractUniqueCustomFields } from "~/features/privacy-requests/dashboard/utils";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";

import { CustomFieldMetadata, CustomFieldMetadataMap } from "../types";

/**
 * Hook that provides access to custom field metadata from the privacy center config.
 * Multiple components can call this hook and they will share the same cached query result via RTK Query.
 *
 * @returns {Object} An object containing:
 *   - customFieldsMap: A map of custom field names to their metadata
 *   - getCustomFieldMetadata: A function to get metadata for a specific field address
 */
export const useCustomFieldMetadata = () => {
  const { data: privacyCenterConfig } = useGetPrivacyCenterConfigQuery();

  // Process custom fields into a map
  const customFieldsMap: CustomFieldMetadataMap = useMemo(() => {
    if (!privacyCenterConfig?.actions) {
      return {};
    }

    return extractUniqueCustomFields(privacyCenterConfig.actions);
  }, [privacyCenterConfig]);

  /**
   * Gets custom field metadata for a given field address.
   * Extracts the field name from addresses like:
   * "privacy_request.custom_privacy_request_fields.{fieldName}"
   *
   * @param fieldAddress - The full field address
   * @returns The custom field metadata or null if not a custom field or not found
   */
  const getCustomFieldMetadata = (
    fieldAddress: string,
  ): CustomFieldMetadata | null => {
    // Check if this is a custom field address
    const customFieldPrefix = "privacy_request.custom_privacy_request_fields.";
    if (!fieldAddress.startsWith(customFieldPrefix)) {
      return null;
    }

    // Extract the field name
    const fieldName = fieldAddress.substring(customFieldPrefix.length);

    // Look up the field in the map
    return customFieldsMap[fieldName] || null;
  };

  return {
    customFieldsMap,
    getCustomFieldMetadata,
  };
};

