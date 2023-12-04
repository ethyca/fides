import {
  Button,
  HStack,
  Input,
  InputGroup,
  InputLeftAddon,
  useToast,
} from "@fidesui/react";
import { useState } from "react";
import { useSelector } from "react-redux";

import { selectToken } from "~/features/auth";
import { requestCSVDownload } from "~/features/consent-reporting/consent-reporting.slice";

const ConsentReporting = () => {
  const [startDate, setStartDate] = useState<string>();
  const [endDate, setEndDate] = useState<string>();

  const token = useSelector(selectToken);
  const toast = useToast();

  const handleDownloadClicked = async () => {
    let message;
    try {
      await requestCSVDownload({ startDate, endDate, token });
    } catch (error) {
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = "An unknown error occurred";
      }
    }
    if (message) {
      toast({
        description: `${message}`,
        duration: 5000,
        status: "error",
      });
    }
  };

  return (
    <HStack gap={4} maxWidth="720px">
      <InputGroup size="sm" flex={1}>
        <InputLeftAddon borderRadius="md">From</InputLeftAddon>
        <Input
          type="date"
          name="From"
          value={startDate}
          max={endDate || undefined}
          onChange={(e) => setStartDate(e.target.value)}
          borderRadius="md"
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
        />
      </InputGroup>
      <Button onClick={handleDownloadClicked} colorScheme="primary" size="sm">
        Download report
      </Button>
    </HStack>
  );
};

export default ConsentReporting;
