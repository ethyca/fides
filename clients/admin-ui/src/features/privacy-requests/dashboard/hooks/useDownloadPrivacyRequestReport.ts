import { useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";

import {
  SearchFilterParams,
  useLazyDownloadPrivacyRequestCsvV2Query,
} from "../../privacy-requests.slice";

const useDownloadPrivacyRequestReport = () => {
  const messageApi = useMessage();

  const [download, { isFetching }] = useLazyDownloadPrivacyRequestCsvV2Query();

  const downloadReport = async (args: SearchFilterParams) => {
    const result = await download(args);
    if (result.isError) {
      const message = getErrorMessage(
        result.error,
        "A problem occurred while generating your privacy request report. Please try again.",
      );
      messageApi.error(message);
    } else {
      const a = document.createElement("a");
      const csvBlob = new Blob([result.data], { type: "text/csv" });
      const csvUrl = window.URL.createObjectURL(csvBlob);
      a.href = csvUrl;
      a.download = `privacy-request-report.csv`;
      a.click();
      a.remove();
      window.URL.revokeObjectURL(csvUrl);
      messageApi.success("Successfully downloaded privacy request report");
    }
  };

  return { downloadReport, isDownloadingReport: isFetching };
};

export default useDownloadPrivacyRequestReport;
