import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import { useLazyDownloadReportQuery } from "../consent-reporting.slice";

const useConsentReportingDownload = () => {
  const toast = useToast();

  const [downloadReportTrigger, { isLoading }] = useLazyDownloadReportQuery();

  const downloadReport = async ({
    startDate,
    endDate,
  }: {
    startDate?: string;
    endDate?: string;
  }) => {
    const result = await downloadReportTrigger({ startDate, endDate });
    if (result.isError) {
      const message = getErrorMessage(
        result.error,
        "A problem occurred while generating your consent report.  Please try again.",
      );
      toast({ status: "error", description: message });
    } else {
      const a = document.createElement("a");
      const csvBlob = new Blob([result.data], { type: "text/csv" });
      a.href = window.URL.createObjectURL(csvBlob);
      a.download = `consent-reports.csv`;
      a.click();
    }
  };

  return { downloadReport, isDownloadingReport: isLoading };
};
export default useConsentReportingDownload;
