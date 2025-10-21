import { useToast } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import { useLazyExportTasksQuery } from "../manual-tasks.slice";

const useDownloadManualTasksReport = () => {
  const toast = useToast();

  const [download, { isFetching }] = useLazyExportTasksQuery();
  const downloadReport = async (args: Parameters<typeof download>["0"]) => {
    const result = await download(args);
    if (result.isError) {
      const message = getErrorMessage(
        result.error,
        "A problem occurred while generating your manual tasks report. Please try again.",
      );
      toast({ status: "error", description: message });
    } else {
      const a = document.createElement("a");
      const csvBlob = new Blob([result.data], { type: "text/csv" });
      const csvUrl = window.URL.createObjectURL(csvBlob);
      a.href = csvUrl;
      a.download = `manual-tasks-report.csv`;
      a.click();
      a.remove();
      window.URL.revokeObjectURL(csvUrl);
      toast({
        status: "success",
        description: "Successfully downloaded Manual Tasks report.",
      });
    }
  };
  return { downloadReport, isDownloadingReport: isFetching };
};

export default useDownloadManualTasksReport;
