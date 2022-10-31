import {
  Box,
  Button,
  CloseButton,
  ModalFooter,
  Spinner,
  Stack,
  Text,
} from "@fidesui/react";
import { useMemo } from "react";

import LargeGreenSpinner from "~/features/common/LargeGreenSpinner";
import { useGetScanResultsQuery } from "~/features/common/plus.slice";

// TODO: update this with whatever progress statuses the backend can return
enum ScanProgress {
  IN_PROGRESS = "in progress",
  COMPLETE = "complete",
  ERROR = "error",
}

/**
 * Currently, runtime scanning is configured before the server starts via
 * fides.toml. Eventually, we'll want to store those credentials via this form, but
 * since that flow doesn't exist yet, this is mostly just a loading screen for now.
 */
const AuthenticateRuntimeForm = () => {
  const { data, isSuccess, error } = useGetScanResultsQuery();

  const progress = useMemo(() => {
    if (error) {
      return ScanProgress.ERROR;
    }
    if (isSuccess) {
      return ScanProgress.COMPLETE;
    }
    return ScanProgress.IN_PROGRESS;
  }, [isSuccess, error]);

  return (
    <Box>
      <Text
        alignItems="center"
        as="b"
        color="gray.900"
        display="flex"
        fontSize="xl"
      >
        Infrastructure scanning {progress}
        <CloseButton
          data-testid="close-scan-in-progress"
          display="inline-block"
          //   onClick={onOpen}
        />
      </Text>

      <Stack alignItems="center">
        <LargeGreenSpinner />
      </Stack>

      <Box data-testid="status">
        {progress === ScanProgress.IN_PROGRESS ? <Spinner /> : null}
        {progress === ScanProgress.ERROR ? (
          <Text color="red">{error}</Text>
        ) : null}
      </Box>
      {data ? (
        <Box data-testid="results">
          <GreenCheckCircle /> {data.systems.length} systems identified
        </Box>
      ) : null}

      {progress === ScanProgress.COMPLETE ? (
        <ModalFooter justifyContent="center">
          <Button
            colorScheme="primary"
            onClick={onFinished}
            data-testid="finished-btn"
            size="sm"
          >
            View Data Map
          </Button>
        </ModalFooter>
      ) : null}
    </Box>
  );
};

export default AuthenticateRuntimeForm;
