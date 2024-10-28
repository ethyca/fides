import { AntButton as Button, Flex, Tooltip } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { DownloadLightIcon } from "~/features/common/Icon";
import Restrict from "~/features/common/Restrict";
import { useGetPrivacyRequestAccessResultsQuery } from "~/features/privacy-requests/privacy-requests.slice";
import { ScopeRegistryEnum } from "~/types/api";

const DownloadAccessResults = ({ requestId }: { requestId: string }) => {
  const { data, isLoading, isError, error } =
    useGetPrivacyRequestAccessResultsQuery({
      privacy_request_id: requestId,
    });

  const downloadButtonTooltip = isError
    ? getErrorMessage(error, "Unable to resolve download URL")
    : "Requests stored locally cannot be downloaded";

  const accessResultUrl = data?.access_result_urls[0] ?? "";

  const canDownload =
    !!accessResultUrl && accessResultUrl !== "your local fides_uploads folder";

  const handleDownloadResultClick = () => {
    const link = document.createElement("a");
    link.href = accessResultUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.click();
    link.remove();
  };

  return (
    <Restrict scopes={[ScopeRegistryEnum.PRIVACY_REQUEST_ACCESS_RESULTS_READ]}>
      <Flex>
        <Tooltip isDisabled={canDownload} label={downloadButtonTooltip}>
          <Button
            onClick={handleDownloadResultClick}
            icon={<DownloadLightIcon />}
            loading={isLoading}
            disabled={!canDownload}
            data-testid="download-results-btn"
          >
            Download request results
          </Button>
        </Tooltip>
      </Flex>
    </Restrict>
  );
};

export default DownloadAccessResults;
