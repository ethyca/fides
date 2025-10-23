import { Dayjs } from "dayjs";
import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import { useLazyDownloadReportQuery } from "../consent-reporting.slice";

const useConsentReportingDownload = () => {
  const toast = useToast();

  const [downloadReportTrigger, { isFetching }] = useLazyDownloadReportQuery();

  const downloadReport = async ({
    startDate,
    endDate,
  }: {
    startDate?: Dayjs | null;
    endDate?: Dayjs | null;
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
      const csvUrl = window.URL.createObjectURL(csvBlob);
      a.href = csvUrl;
      a.download = `consent-reports.csv`;
      a.click();
      window.URL.revokeObjectURL(csvUrl);
    }
  };

  return { downloadReport, isDownloadingReport: isFetching };
};
export default useConsentReportingDownload;
