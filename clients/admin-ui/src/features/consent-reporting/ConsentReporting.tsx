import {
  AntButton as Button,
  HStack,
  Input,
  InputGroup,
  InputLeftAddon,
  useToast,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useLazyDownloadReportQuery } from "~/features/consent-reporting/consent-reporting.slice";

const ConsentReporting = () => {
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  const toast = useToast();

  const [downloadReportTrigger, { isLoading }] = useLazyDownloadReportQuery();

  const handleDownloadClicked = async () => {
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

  return (
    <HStack gap={4} maxWidth="720px" data-testid="consent-reporting">
      <InputGroup size="sm" flex={1}>
        <InputLeftAddon borderRadius="md">From</InputLeftAddon>
        <Input
          type="date"
          name="From"
          value={startDate}
          max={endDate || undefined}
          onChange={(e) => setStartDate(e.target.value)}
          borderRadius="md"
          data-testid="input-from-date"
        />
      </InputGroup>
      <InputGroup size="sm" flex={1}>
        <InputLeftAddon borderRadius="md">To</InputLeftAddon>
        <Input
          type="date"
          name="To"
          value={endDate}
          min={startDate || undefined}
          onChange={(e) => setEndDate(e.target.value)}
          borderRadius="md"
          data-testid="input-to-date"
        />
      </InputGroup>
      <Button
        onClick={handleDownloadClicked}
        loading={isLoading}
        type="primary"
        data-testid="download-btn"
      >
        Download report
      </Button>
    </HStack>
  );
};

export default ConsentReporting;
