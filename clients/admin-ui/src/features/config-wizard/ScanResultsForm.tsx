import {
  Box,
  Button,
  Heading,
  HStack,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useRouter } from "next/router";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  ColumnDropdown,
  ColumnMetadata,
} from "~/features/common/ColumnDropdown";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import { System } from "~/types/api";

import { useFeatures } from "../common/features.slice";
import WarningModal from "../common/WarningModal";
import { useCreateSystemMutation } from "../system";
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

interface Props {
  manualSystemSetupChosen: boolean;
}

const ScanResultsForm = ({ manualSystemSetupChosen }: Props) => {
  const systems = useAppSelector(selectSystemsForReview);
  const dispatch = useAppDispatch();
  const router = useRouter();
  const {
    isOpen: isWarningOpen,
    onOpen: onWarningOpen,
    onClose: onWarningClose,
  } = useDisclosure();
  const [createSystem] = useCreateSystemMutation();
  const [selectedSystems, setSelectedSystems] = useState<System[]>(systems);
  const features = useFeatures();
  const [selectedColumns, setSelectedColumns] =
    useState<ColumnMetadata[]>(ALL_COLUMNS);

  const createSystems = async () => {
    await selectedSystems.forEach((system: System) => createSystem(system));
  };

  const confirmRegisterSelectedSystems = () => {
    if (manualSystemSetupChosen) {
      dispatch(chooseSystemsForReview(selectedSystems.map((s) => s.fides_key)));
      return dispatch(changeStep());
    } 
      createSystems();
    
    return features.plus ? router.push(`/datamap`) : router.push(`/system`);
  };

  const handleSubmit = () => {
    if (systems.length > selectedSystems.length) {
      return onWarningOpen();
    }
    if (manualSystemSetupChosen) {
      return confirmRegisterSelectedSystems();
    }
    createSystems();
    return features.plus ? router.push(`/datamap`) : router.push(`/system`);
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

        <Box>
          <Text>
            Below are search results for {region}. Please select and register
            the systems you would like to maintain in your mapping and reports.
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
          <Button variant="outline" onClick={handleCancel}>
            Back
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
