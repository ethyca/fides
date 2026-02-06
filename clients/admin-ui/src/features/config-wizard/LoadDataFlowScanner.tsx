import { Flex, useMessage } from "fidesui";
import { useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import {
  isErrorResult,
  ParsedError,
  parseError,
} from "~/features/common/helpers";
import {
  useLazyGetLatestScanDiffQuery,
  useUpdateScanMutation,
} from "~/features/plus/plus.slice";
import { isAPIError, RTKErrorResult } from "~/types/errors";

import ErrorPage from "../common/errors/ErrorPage";
import { changeStep, setSystemsForReview } from "./config-wizard.slice";
import ScannerLoading from "./ScannerLoading";

/**
 * Currently, data flow scanning is configured before the server starts via
 * fides.toml. Eventually, we'll want to store those credentials via this form, but
 * since that flow doesn't exist yet, this is mostly just a loading screen for now.
 */
const LoadDataFlowScanner = () => {
  const dispatch = useAppDispatch();
  const messageApi = useMessage();
  const [triggerGetDiff] = useLazyGetLatestScanDiffQuery();
  const [updateScanMutation, { data: scanResults }] = useUpdateScanMutation();
  const [scannerError, setScannerError] = useState<ParsedError>();
  const [isRescan, setIsRescan] = useState(false);

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error, {
      status: 500,
      message:
        "Our system encountered a problem while scanning your infrastructure.",
    });
    setScannerError(parsedError);
  };

  // Call scan as soon as this component mounts
  useEffect(() => {
    const handleScan = async () => {
      // Check whether or not this is the user's first scan
      const { error: latestScanError } = await triggerGetDiff();
      const isFirstScan =
        !!latestScanError &&
        isAPIError(latestScanError) &&
        latestScanError.status === 404;
      setIsRescan(!isFirstScan);

      const result = await updateScanMutation({ classify: true });
      if (isErrorResult(result)) {
        handleError(result.error);
      }
    };

    handleScan();
  }, [updateScanMutation, triggerGetDiff]);

  /**
   * When the scan is finished, handle the results. This is separated into two useEffects
   * in order not to trigger the initial scan again.
   */
  useEffect(() => {
    const handleResults = async () => {
      if (scanResults) {
        const { data: diff } = await triggerGetDiff();
        const systemsToRegister = isRescan
          ? diff?.added_systems || []
          : scanResults.systems;

        messageApi.success(
          `Your scan was successfully completed, with ${systemsToRegister.length} new systems detected!`,
        );
        dispatch(setSystemsForReview(systemsToRegister));
        dispatch(changeStep());
      }
    };
    handleResults();
  }, [scanResults, messageApi, dispatch, isRescan, triggerGetDiff]);

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  if (scannerError) {
    return (
      <Flex className="w-full">
        <ErrorPage
          error={scannerError}
          fullScreen={false}
          showReload={false}
          actions={[
            {
              label: "Cancel",
              onClick: handleCancel,
              "data-testid": "cancel-btn",
            },
          ]}
        />
      </Flex>
    );
  }

  return (
    <ScannerLoading
      title="Infrastructure scanning in progress"
      onClose={handleCancel}
    />
  );
};

export default LoadDataFlowScanner;
