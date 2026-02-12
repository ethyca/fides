import { useChakraToast as useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import type { AssetReportingFilters } from "../asset-reporting.slice";
import { useLazyDownloadAssetReportQuery } from "../asset-reporting.slice";

const useAssetReportingDownload = () => {
  const toast = useToast();
  const [downloadTrigger, { isFetching }] = useLazyDownloadAssetReportQuery();

  const downloadReport = async (filters: AssetReportingFilters) => {
    const result = await downloadTrigger(filters);

    if (result.isError) {
      const message = getErrorMessage(
        result.error,
        "A problem occurred while generating your asset report. Please try again.",
      );
      toast({ status: "error", description: message });
    } else {
      const csvBlob = new Blob([result.data ?? ""], { type: "text/csv" });
      const csvUrl = window.URL.createObjectURL(csvBlob);
      const a = document.createElement("a");
      a.href = csvUrl;
      a.download = `asset-report-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(csvUrl);

      toast({
        status: "success",
        description: "Asset report downloaded successfully.",
      });
    }
  };

  return { downloadReport, isDownloadingReport: isFetching };
};

export default useAssetReportingDownload;
