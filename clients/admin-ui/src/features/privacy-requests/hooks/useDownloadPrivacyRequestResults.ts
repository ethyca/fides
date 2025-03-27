import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import { getActionTypes } from "~/features/common/RequestType";
import { useHasPermission } from "~/features/common/Restrict";
import {
  ActionType,
  PrivacyRequestStatus,
  ScopeRegistryEnum,
} from "~/types/api";

import { useGetPrivacyRequestAccessResultsQuery } from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

const useDownloadPrivacyRequestResults = ({
  privacyRequest,
}: {
  privacyRequest: PrivacyRequestEntity;
}) => {
  const isDownloadResultsFlagEnabled =
    useFeatures()?.flags?.downloadAccessRequestResults;
  const isCompletedRequest =
    privacyRequest.status === PrivacyRequestStatus.COMPLETE;

  const isActionRequest = getActionTypes(privacyRequest.policy.rules).includes(
    ActionType.ACCESS,
  );

  const hasPermissionsToAccessResults = useHasPermission([
    ScopeRegistryEnum.PRIVACY_REQUEST_ACCESS_RESULTS_READ,
  ]);

  const { data, isLoading, isError, error } =
    useGetPrivacyRequestAccessResultsQuery({
      privacy_request_id: privacyRequest.id,
    });
  const accessResultUrl = data?.access_result_urls[0] ?? "";
  const downloadLinkIsAvailable =
    !!accessResultUrl && accessResultUrl !== "your local fides_uploads folder";

  let infoTooltip = null;
  if (isError) {
    infoTooltip = getErrorMessage(error, "Unable to resolve download URL");
  } else if (!downloadLinkIsAvailable) {
    infoTooltip = "Requests stored locally cannot be downloaded";
  }

  const downloadResults = () => {
    const link = document.createElement("a");
    link.href = accessResultUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.click();
    link.remove();
  };

  const showDownloadResults =
    isDownloadResultsFlagEnabled &&
    hasPermissionsToAccessResults &&
    isActionRequest &&
    isCompletedRequest;

  return {
    showDownloadResults,
    downloadResults,
    infoTooltip,
    isLoading,
    isDisabled: !downloadLinkIsAvailable,
  };
};
export default useDownloadPrivacyRequestResults;
