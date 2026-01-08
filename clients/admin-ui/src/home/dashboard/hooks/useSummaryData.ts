import { useMemo } from "react";

import palette from "fidesui/src/palette/palette.module.scss";
import { useFeatures } from "~/features/common/features";
import { PrivacyRequestStatus } from "~/types/api";

import { DiffStatus } from "~/types/api";

import {
  useGetPrivacyRequestCountsQuery,
  useGetSystemCountQuery,
  useGetDataCatalogDatasetCountQuery,
  useGetWebsiteInfrastructureAggregatesQuery,
  useGetDatastoreMonitorAggregatesQuery,
} from "../dashboard.slice";
import type { SummaryData } from "../types";

/**
 * Hook for fetching and transforming summary data for the dashboard
 * Aggregates data from multiple API endpoints into the SummaryData format
 */
export const useSummaryData = (): {
  data: SummaryData | undefined;
  isLoading: boolean;
  error: unknown;
} => {
  const { plus } = useFeatures();

  // Fetch privacy request counts by status
  const {
    data: pendingCount,
    isLoading: isLoadingPending,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.PENDING],
  });
  const {
    data: identityUnverifiedCount,
    isLoading: isLoadingIdentityUnverified,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.IDENTITY_UNVERIFIED],
  });
  const {
    data: approvedCount,
    isLoading: isLoadingApproved,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.APPROVED],
  });
  const {
    data: inProcessingCount,
    isLoading: isLoadingInProcessing,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.IN_PROCESSING],
  });
  const {
    data: awaitingEmailSendCount,
    isLoading: isLoadingAwaitingEmailSend,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.AWAITING_EMAIL_SEND],
  });
  const {
    data: pausedCount,
    isLoading: isLoadingPaused,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.PAUSED],
  });
  const {
    data: requiresInputCount,
    isLoading: isLoadingRequiresInput,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.REQUIRES_INPUT],
  });
  const {
    data: requiresManualFinalizationCount,
    isLoading: isLoadingRequiresManualFinalization,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION],
  });
  const {
    data: errorCount,
    isLoading: isLoadingError,
  } = useGetPrivacyRequestCountsQuery({
    status: [PrivacyRequestStatus.ERROR],
  });

  // Fetch system count
  const {
    data: systemCount,
    isLoading: isLoadingSystems,
  } = useGetSystemCountQuery();

  // Fetch data-catalog dataset count (Fidesplus)
  // Only fetch if plus is available, as this endpoint only exists in Fidesplus
  const {
    data: datasetCount,
    isLoading: isLoadingDatasets,
  } = useGetDataCatalogDatasetCountQuery(undefined, {
    skip: !plus,
  });

  // Fetch website/infrastructure monitor aggregates (Asset Detection)
  const {
    data: websiteInfraAggregates,
    isLoading: isLoadingWebsiteInfra,
  } = useGetWebsiteInfrastructureAggregatesQuery(undefined, {
    skip: !plus,
  });

  // Fetch datastore monitor aggregates (Data Discovery)
  const {
    data: datastoreAggregates,
    isLoading: isLoadingDatastore,
  } = useGetDatastoreMonitorAggregatesQuery(undefined, {
    skip: !plus,
  });

  const isLoading =
    isLoadingPending ||
    isLoadingIdentityUnverified ||
    isLoadingApproved ||
    isLoadingInProcessing ||
    isLoadingAwaitingEmailSend ||
    isLoadingPaused ||
    isLoadingRequiresInput ||
    isLoadingRequiresManualFinalization ||
    isLoadingError ||
    isLoadingSystems ||
    isLoadingDatasets ||
    (plus && isLoadingWebsiteInfra) ||
    (plus && isLoadingDatastore);

  const summaryData: SummaryData | undefined = useMemo(() => {
    // Wait for all data to be available (including 0 values which are valid)
    // Note: datasetCount, websiteInfraAggregates, and datastoreAggregates may be undefined
    // if plus is not available (queries are skipped). In that case, we treat them as 0.
    if (
      pendingCount === undefined ||
      identityUnverifiedCount === undefined ||
      approvedCount === undefined ||
      inProcessingCount === undefined ||
      awaitingEmailSendCount === undefined ||
      pausedCount === undefined ||
      requiresInputCount === undefined ||
      requiresManualFinalizationCount === undefined ||
      errorCount === undefined ||
      systemCount === undefined ||
      (plus && websiteInfraAggregates === undefined) ||
      (plus && datastoreAggregates === undefined)
    ) {
      return undefined;
    }

    // Calculate "Need Review" total: PENDING + IDENTITY_UNVERIFIED + ERROR + REQUIRES_INPUT + REQUIRES_MANUAL_FINALIZATION
    const totalNeedReview =
      (pendingCount.total ?? 0) +
      (identityUnverifiedCount.total ?? 0) +
      (errorCount.total ?? 0) +
      (requiresInputCount.total ?? 0) +
      (requiresManualFinalizationCount.total ?? 0);

    // Calculate breakdown values
    // "New" = PENDING + IDENTITY_UNVERIFIED
    const newCount =
      (pendingCount.total ?? 0) + (identityUnverifiedCount.total ?? 0);

    // "In Progress" = APPROVED + IN_PROCESSING + AWAITING_EMAIL_SEND + PAUSED + REQUIRES_INPUT + REQUIRES_MANUAL_FINALIZATION
    const inProgressCount =
      (approvedCount.total ?? 0) +
      (inProcessingCount.total ?? 0) +
      (awaitingEmailSendCount.total ?? 0) +
      (pausedCount.total ?? 0) +
      (requiresInputCount.total ?? 0) +
      (requiresManualFinalizationCount.total ?? 0);

    // "Action Required" = PENDING + IDENTITY_UNVERIFIED + ERROR + REQUIRES_INPUT + REQUIRES_MANUAL_FINALIZATION
    const actionRequiredCount =
      (pendingCount.total ?? 0) +
      (identityUnverifiedCount.total ?? 0) +
      (errorCount.total ?? 0) +
      (requiresInputCount.total ?? 0) +
      (requiresManualFinalizationCount.total ?? 0);

    // "Errors" = ERROR
    const errorsCount = errorCount.total ?? 0;

    return {
      privacyRequests: {
        total: totalNeedReview,
        totalLabel: "Need Review",
        breakdown: [
          {
            label: "New",
            value: newCount,
            color: palette.FIDESUI_INFO,
          },
          {
            label: "In Progress",
            value: inProgressCount,
            color: palette.FIDESUI_WARNING,
          },
          {
            label: "Action Required",
            value: actionRequiredCount,
            color: palette.FIDESUI_NEUTRAL_700,
          },
          {
            label: "Errors",
            value: errorsCount,
            color: palette.FIDESUI_ERROR,
          },
        ],
      },
      systemDetection: {
        // Asset Detection: Need Review = In review + Uncategorized
        // For website/infrastructure: In review = CLASSIFICATION_ADDITION + CLASSIFICATION_UPDATE
        // Uncategorized = ADDITION, Categorized = APPROVED
        total:
          plus && websiteInfraAggregates
            ? (websiteInfraAggregates.in_review ?? 0) +
              (websiteInfraAggregates.uncategorized ?? 0)
            : 0,
        totalLabel: "Need Review",
        breakdown: [
          {
            label: "Detected",
            value:
              plus && websiteInfraAggregates
                ? websiteInfraAggregates.total ?? 0
                : 0,
            color: palette.FIDESUI_INFO,
          },
          {
            label: "Review Needed",
            value:
              plus && websiteInfraAggregates
                ? websiteInfraAggregates.in_review ?? 0
                : 0,
            color: palette.FIDESUI_WARNING,
          },
          {
            label: "Uncategorized",
            value:
              plus && websiteInfraAggregates
                ? websiteInfraAggregates.uncategorized ?? 0
                : 0,
            color: palette.FIDESUI_NEUTRAL_400,
          },
          {
            label: "Categorized",
            value:
              plus && websiteInfraAggregates
                ? websiteInfraAggregates.categorized ?? 0
                : 0,
            color: palette.FIDESUI_SUCCESS,
          },
        ],
      },
      dataClassification: {
        // Data Discovery: Need Review = In review + Unlabeled + Classifying + Approved
        // Review Needed = In review + Classifying + Approved
        // Unclassified = Unlabeled
        // Classified = classified + Approved = in_review + approved (since in_review includes classified fields)
        total:
          plus && datastoreAggregates
            ? (datastoreAggregates.in_review ?? 0) +
              (datastoreAggregates.unlabeled ?? 0) +
              (datastoreAggregates.classifying ?? 0) +
              (datastoreAggregates.approved ?? 0)
            : 0,
        totalLabel: "Need Review",
        breakdown: [
          {
            label: "Discovered",
            value:
              plus && datastoreAggregates
                ? datastoreAggregates.total ?? 0
                : 0,
            color: palette.FIDESUI_INFO,
          },
          {
            label: "Review Needed",
            value:
              plus && datastoreAggregates
                ? (datastoreAggregates.in_review ?? 0) +
                  (datastoreAggregates.classifying ?? 0) +
                  (datastoreAggregates.approved ?? 0)
                : 0,
            color: palette.FIDESUI_WARNING,
          },
          {
            label: "Unclassified",
            value:
              plus && datastoreAggregates
                ? datastoreAggregates.unlabeled ?? 0
                : 0,
            color: palette.FIDESUI_NEUTRAL_400,
          },
          {
            label: "Classified",
            value:
              plus && datastoreAggregates
                ? (datastoreAggregates.in_review ?? 0) +
                  (datastoreAggregates.approved ?? 0)
                : 0,
            color: palette.FIDESUI_SUCCESS,
          },
        ],
      },
    };
  }, [
    pendingCount,
    identityUnverifiedCount,
    approvedCount,
    inProcessingCount,
    awaitingEmailSendCount,
    pausedCount,
    requiresInputCount,
    requiresManualFinalizationCount,
    errorCount,
    systemCount,
    datasetCount,
    websiteInfraAggregates,
    datastoreAggregates,
    plus,
  ]);

  return {
    data: summaryData,
    isLoading,
    error: null, // TODO: Aggregate errors from all queries
  };
};
