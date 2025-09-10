import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import { useLazyDownloadPrivacyRequestCsvQuery } from "../privacy-requests.slice";

const useDownloadPrivacyRequestReport = () => {
  const toast = useToast();

  const [download, { isFetching }] = useLazyDownloadPrivacyRequestCsvQuery();
  const downloadReport = async (args: Parameters<typeof download>["0"]) => {
    const result = await download(args);
    if (result.isError) {
      const message = getErrorMessage(
        result.error,
        "A problem occurred while generating your privacy request report.  Please try again.",
      );
      toast({ status: "error", description: message });
    } else {
      const a = document.createElement("a");
      const csvBlob = new Blob([result.data], { type: "text/csv" });
      const csvUrl = window.URL.createObjectURL(csvBlob);
      a.href = csvUrl;
      a.download = `privacy-request-report.csv`;
      a.click();
      a.remove();
      window.URL.revokeObjectURL(csvUrl);
      toast({
        status: "success",
        description: "Successfully downloaded Privacy Request report.",
      });
    }
  };
  return { downloadReport, isDownloadingReport: isFetching };
};

export default useDownloadPrivacyRequestReport;
