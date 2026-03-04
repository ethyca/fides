import { useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { useLazyGetPrivacyRequestDiagnosticsQuery } from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

const isLikelyRemoteUrl = (value: string) => /^https?:\/\//i.test(value);

const useDownloadPrivacyRequestDiagnostics = ({
  privacyRequest,
}: {
  privacyRequest: PrivacyRequestEntity;
}) => {
  const message = useMessage();

  const hasPermissionsToReadPrivacyRequests = useHasPermission([
    ScopeRegistryEnum.PRIVACY_REQUEST_READ,
  ]);

  const [fetchDiagnostics, { isFetching }] =
    useLazyGetPrivacyRequestDiagnosticsQuery();

  const downloadTroubleshootingData = async () => {
    const result = await fetchDiagnostics(
      { privacy_request_id: privacyRequest.id },
      true,
    );

    if ("error" in result) {
      if (result.error) {
        message.error(
          getErrorMessage(result.error, "Unable to resolve download URL"),
        );
      } else {
        message.error("Unable to resolve download URL");
      }
      return;
    }

    const downloadUrl = result.data?.download_url ?? "";
    if (!downloadUrl) {
      message.error("Unable to resolve download URL");
      return;
    }

    if (!isLikelyRemoteUrl(downloadUrl)) {
      message.info("Troubleshooting data stored locally cannot be downloaded");
      return;
    }

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.click();
    link.remove();
  };

  const showDownloadTroubleshootingData = hasPermissionsToReadPrivacyRequests;

  return {
    showDownloadTroubleshootingData,
    downloadTroubleshootingData,
    isLoading: isFetching,
  };
};

export default useDownloadPrivacyRequestDiagnostics;
