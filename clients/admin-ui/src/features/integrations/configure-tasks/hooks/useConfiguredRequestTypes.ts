import { useMemo } from "react";

import { useGetManualFieldsQuery } from "~/features/datastore-connections/connection-manual-fields.slice";
import { ManualFieldRequestType } from "~/types/api";

interface UseConfiguredRequestTypesProps {
  connectionKey: string;
}

interface UseConfiguredRequestTypesResult {
  /**
   * Set of request types that have at least one manual task configured
   */
  configuredRequestTypes: Set<ManualFieldRequestType>;
  /**
   * Whether ONLY consent tasks are configured (no access or erasure tasks)
   */
  isConsentOnly: boolean;
  /**
   * Whether consent tasks are configured (regardless of other types)
   */
  hasConsentTasks: boolean;
  /**
   * Whether access or erasure tasks are configured
   */
  hasAccessOrErasureTasks: boolean;
  /**
   * Whether the data is still loading
   */
  isLoading: boolean;
}

/**
 * Hook to determine which request types have manual tasks configured for a connection.
 * This is used to filter condition field options based on what's actually configured.
 *
 * For consent-only configurations, certain condition fields should be hidden because:
 * - Dataset fields are not evaluated (consent DSRs don't have data flow between nodes)
 * - Some privacy request fields like due_date are not available for consent
 */
export const useConfiguredRequestTypes = ({
  connectionKey,
}: UseConfiguredRequestTypesProps): UseConfiguredRequestTypesResult => {
  const { data: manualFields, isLoading } = useGetManualFieldsQuery(
    { connectionKey },
    { skip: !connectionKey },
  );

  const result = useMemo(() => {
    const configuredRequestTypes = new Set<ManualFieldRequestType>();

    // Handle the case where manualFields is an array
    if (manualFields && Array.isArray(manualFields)) {
      manualFields.forEach((field) => {
        configuredRequestTypes.add(field.request_type);
      });
    }

    const hasConsentTasks = configuredRequestTypes.has(
      ManualFieldRequestType.CONSENT,
    );
    const hasAccessOrErasureTasks =
      configuredRequestTypes.has(ManualFieldRequestType.ACCESS) ||
      configuredRequestTypes.has(ManualFieldRequestType.ERASURE);

    // Consent-only means consent tasks exist AND no access/erasure tasks exist
    const isConsentOnly = hasConsentTasks && !hasAccessOrErasureTasks;

    return {
      configuredRequestTypes,
      isConsentOnly,
      hasConsentTasks,
      hasAccessOrErasureTasks,
    };
  }, [manualFields]);

  return {
    ...result,
    isLoading,
  };
};
