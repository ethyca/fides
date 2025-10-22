import { useToast } from "fidesui";

import { useLazyExportExternalTasksQuery } from "../../external-manual-tasks.slice";

const useDownloadExternalTasksReport = () => {
  const toast = useToast();

  const [download, { isFetching }] = useLazyExportExternalTasksQuery();
  const downloadReport = async (args: Parameters<typeof download>["0"]) => {
    const result = await download(args);
    if (result.isError) {
      const errorMessage =
        "error" in result && typeof result.error === "object" && result.error
          ? JSON.stringify(result.error)
          : "A problem occurred while generating your external tasks report. Please try again.";
      toast({ status: "error", description: errorMessage });
    } else if (result.data) {
      const a = document.createElement("a");
      const csvBlob = new Blob([result.data], { type: "text/csv" });
      const csvUrl = window.URL.createObjectURL(csvBlob);
      a.href = csvUrl;
      a.download = `external-tasks-report.csv`;
      a.click();
      a.remove();
      window.URL.revokeObjectURL(csvUrl);
      toast({
        status: "success",
        description: "Successfully downloaded external tasks report.",
      });
    }
  };
  return { downloadReport, isDownloadingReport: isFetching };
};

export default useDownloadExternalTasksReport;
