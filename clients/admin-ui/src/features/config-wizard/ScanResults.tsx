import {
  AntButton as Button,
  Box,
  Heading,
  HStack,
  Stack,
  Text,
  useDisclosure,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ColumnDropdown, {
  ColumnMetadata,
} from "~/features/common/ColumnDropdown";
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { useSystemOrDatamapRoute } from "~/features/common/hooks/useSystemOrDatamapRoute";
import WarningModal from "~/features/common/modals/WarningModal";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import { useUpsertSystemsMutation } from "~/features/system";
import { System } from "~/types/api";

import {
  changeStep,
  reset,
  selectSystemsForReview,
} from "./config-wizard.slice";

const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Name", attribute: "name" },
  { name: "System type", attribute: "system_type" },
  { name: "Resource ID", attribute: "fidesctl_meta.resource_id" },
];

const ScanResults = () => {
  const systems = useAppSelector(selectSystemsForReview);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { systemOrDatamapRoute } = useSystemOrDatamapRoute();

  const {
    isOpen: isWarningOpen,
    onOpen: onWarningOpen,
    onClose: onWarningClose,
  } = useDisclosure();
  const [upsertSystems] = useUpsertSystemsMutation();
  const [selectedSystems, setSelectedSystems] = useState<System[]>(systems);
  const [selectedColumns, setSelectedColumns] =
    useState<ColumnMetadata[]>(ALL_COLUMNS);
  const { handleError } = useAPIHelper();

  /**
   * Wrapper around router.push which also cleans up the config wizard state
   * so that if we navigate back, the flow will start over. This is useful here
   * as this is the last step of the wizard, so when we navigate away, we can
   * reset the state.
   */
  const navigateAndReset = (route: string) => {
    router.push(route).then(() => {
      dispatch(reset());
    });
  };

  const confirmRegisterSelectedSystems = async () => {
    const response = await upsertSystems(selectedSystems);

    if (isErrorResult(response)) {
      return handleError(response.error);
    }

    return navigateAndReset(systemOrDatamapRoute);
  };

  const handleSubmit = () => {
    if (systems.length > selectedSystems.length) {
      onWarningOpen();
    } else {
      confirmRegisterSelectedSystems();
    }
  };

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  const warningMessage = (
    <Text color="gray.500" mb={3}>
      You’re registering {selectedSystems.length} of {systems.length} systems
      available. Do you want to continue with registration or cancel and
      register all systems now?
    </Text>
  );

  return (
    <Box maxW="full">
      <Stack spacing={10}>
        <Heading as="h3" size="lg" data-testid="scan-results">
          Scan results
        </Heading>

        {systems.length === 0 ? (
          <>
            <Text data-testid="no-results">
              No results were found for your infrastructure scan.
            </Text>
            <HStack>
              <Button onClick={handleCancel} data-testid="back-btn">
                Back
              </Button>
            </HStack>
          </>
        ) : (
          <>
            <Box>
              <Text>
                Below are the results of your infrastructure scan. To continue,
                select the systems you would like registered in your data map
                and reports.
              </Text>
              <Box display="flex" justifyContent="end">
                <ColumnDropdown
                  allColumns={ALL_COLUMNS}
                  selectedColumns={selectedColumns}
                  onChange={setSelectedColumns}
                />
              </Box>
            </Box>
            <SystemsCheckboxTable
              allSystems={systems}
              checked={selectedSystems}
              onChange={setSelectedSystems}
              columns={selectedColumns}
            />

            <HStack>
              <Button onClick={handleCancel}>Back</Button>
              <Button
                onClick={handleSubmit}
                type="primary"
                disabled={selectedSystems.length === 0}
                data-testid="register-btn"
              >
                Register selected systems
              </Button>
            </HStack>
          </>
        )}
      </Stack>

      <WarningModal
        title="Warning"
        message={warningMessage}
        handleConfirm={confirmRegisterSelectedSystems}
        isOpen={isWarningOpen}
        onClose={onWarningClose}
      />
    </Box>
  );
};

export default ScanResults;
