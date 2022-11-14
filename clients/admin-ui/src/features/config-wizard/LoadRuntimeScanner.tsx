import { Box, Button, Stack, useToast } from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { useUpdateScanMutation } from "~/features/plus/plus.slice";
import { RTKErrorResult } from "~/types/errors";

import { changeStep, setSystemsForReview } from "./config-wizard.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

/**
 * Currently, runtime scanning is configured before the server starts via
 * fides.toml. Eventually, we'll want to store those credentials via this form, but
 * since that flow doesn't exist yet, this is mostly just a loading screen for now.
 */
const LoadRuntimeScanner = () => {
  const dispatch = useAppDispatch();
  const toast = useToast();
  const [updateScanMutation] = useUpdateScanMutation();
  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message:
        "Our system encountered a problem while scanning your infrastructure.",
    });
    setScannerError(parsedError);
  };

  useEffect(() => {
    const handleScan = async () => {
      const result = await updateScanMutation({ classify: true });
      if (isErrorResult(result)) {
        handleError(result.error);
      } else {
        const { data } = result;
        toast(
          successToastParams(
            `Your scan was successfully completed, with ${data.systems.length} new systems detected!`
          )
        );
        dispatch(setSystemsForReview(data.systems));
        dispatch(changeStep());
      }
    };

    handleScan();
  }, [updateScanMutation, dispatch, toast]);

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  if (scannerError) {
    return (
      <Stack>
        <ScannerError error={scannerError} />
        <Box>
          <Button
            variant="outline"
            onClick={handleCancel}
            data-testid="cancel-btn"
          >
            Cancel
          </Button>
        </Box>
      </Stack>
    );
  }

  return (
    <ScannerLoading
      title="Infrastructure scanning in progress"
      onClose={handleCancel}
    />
  );
};

export default LoadRuntimeScanner;
