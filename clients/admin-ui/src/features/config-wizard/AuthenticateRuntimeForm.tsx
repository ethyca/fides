import { useToast } from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { ParsedError, parseError } from "~/features/common/helpers";
import { useGetScanResultsQuery } from "~/features/common/plus.slice";
import { successToastParams } from "~/features/common/toast";
import { RTKErrorResult } from "~/types/errors";

import { changeStep } from "./config-wizard.slice";
import ScannerError from "./ScannerError";
import ScannerLoading from "./ScannerLoading";

/**
 * Currently, runtime scanning is configured before the server starts via
 * fides.toml. Eventually, we'll want to store those credentials via this form, but
 * since that flow doesn't exist yet, this is mostly just a loading screen for now.
 */
const AuthenticateRuntimeForm = () => {
  const dispatch = useAppDispatch();
  const toast = useToast();
  const { data, error: queryError } = useGetScanResultsQuery();
  const [scannerError, setScannerError] = useState<ParsedError>();

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message:
        "Our system encountered a problem while scanning your infrastructure.",
    });
    setScannerError(parsedError);
  };

  // Handle success, which will redirect to another view
  useEffect(() => {
    if (data) {
      toast(
        successToastParams(
          `Your scan was successfully completed, with ${data.systems.length} new systems detected!`
        )
      );
      dispatch(changeStep());
    }
  }, [data, dispatch, toast]);

  // Handle errors
  useEffect(() => {
    if (queryError) {
      handleError(queryError);
    }
  }, [queryError]);

  if (scannerError) {
    <ScannerError error={scannerError} />;
  }

  return (
    <ScannerLoading
      title="Infrastructure scanning in progress"
      onClose={handleCancel}
    />
  );
};

export default AuthenticateRuntimeForm;
