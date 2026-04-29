import { useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import { useLazyDownloadDataPurposesCsvQuery } from "./data-purpose.slice";

const useDownloadRoPA = () => {
  const message = useMessage();

  const [download, { isFetching }] = useLazyDownloadDataPurposesCsvQuery();

  const downloadRoPA = async (args: Parameters<typeof download>["0"] = {}) => {
    const result = await download(args);
    if (result.isError) {
      message.error(
        getErrorMessage(
          result.error,
          "A problem occurred while generating your RoPA report. Please try again.",
        ),
      );
      return;
    }
    const csvBlob = new Blob([result.data!], { type: "text/csv" });
    const csvUrl = window.URL.createObjectURL(csvBlob);
    const anchor = document.createElement("a");
    anchor.href = csvUrl;
    anchor.download = "ropa.csv";
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(csvUrl);
    message.success("Successfully downloaded RoPA report.");
  };

  return { downloadRoPA, isDownloadingRoPA: isFetching };
};

export default useDownloadRoPA;
