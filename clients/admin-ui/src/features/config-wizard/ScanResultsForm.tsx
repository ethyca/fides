import {
  Box,
  Button,
  Heading,
  HStack,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import React, { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { ColumnMetadata } from "~/features/common/ColumnDropdown";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import WarningModal from "~/features/common/WarningModal";
import { System } from "~/types/api";

import {
  changeStep,
  chooseSystemsForReview,
  selectSystemsForReview,
} from "./config-wizard.slice";

const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Name", attribute: "name" },
  { name: "System type", attribute: "system_type" },
  { name: "Resource ID", attribute: "fidesctl_meta.resource_id" },
];

const ScanResultsForm = () => {
  const systems = useAppSelector(selectSystemsForReview);
  const dispatch = useAppDispatch();
  const {
    isOpen: isWarningOpen,
    onOpen: onWarningOpen,
    onClose: onWarningClose,
  } = useDisclosure();
  const [selectedSystems, setSelectedSystems] = useState<System[]>(systems);

  const confirmRegisterSelectedSystems = () => {
    dispatch(chooseSystemsForReview(selectedSystems.map((s) => s.fides_key)));
    dispatch(changeStep());
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

  // TODO: Store the region the user submitted through the form.
  const region = "the specified region";

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

        <Text>
          Below are search results for {region}. Please select and register the
          systems you would like to maintain in your mapping and reports.
        </Text>

        <SystemsCheckboxTable
          allSystems={systems}
          checked={selectedSystems}
          onChange={setSelectedSystems}
          columns={ALL_COLUMNS}
        />

        <HStack>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            isDisabled={selectedSystems.length === 0}
            data-testid="register-btn"
            onClick={handleSubmit}
          >
            Register selected systems
          </Button>
        </HStack>
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

export default ScanResultsForm;
