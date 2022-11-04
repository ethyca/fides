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
import { useFeatures } from "~/features/common/features.slice";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { resolveLink } from "~/features/common/nav/zone-config";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import WarningModal from "~/features/common/WarningModal";
import { useUpsertSystemsMutation } from "~/features/system";
import { System } from "~/types/api";
import { isErrorResult } from "../common/helpers";

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
  const router = useRouter();
  const {
    isOpen: isWarningOpen,
    onOpen: onWarningOpen,
    onClose: onWarningClose,
  } = useDisclosure();
  const [upsertSystems] = useUpsertSystemsMutation();
  const [selectedSystems, setSelectedSystems] = useState<System[]>(systems);
  const features = useFeatures();
  const [selectedColumns, setSelectedColumns] =
    useState<ColumnMetadata[]>(ALL_COLUMNS);
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();

  const confirmRegisterSelectedSystems = async () => {
    dispatch(chooseSystemsForReview(selectedSystems.map((s) => s.fides_key)));
    const response = await upsertSystems(selectedSystems);

    if (isErrorResult(response)) {
      handleError(response.error);
    } else {
      const datamapRoute = resolveLink({
        href: "/datamap",
        basePath: "/",
      });

      successAlert(
        `You have successfully added ${selectedSystems?.length} systems to your Data Map`,
        `${selectedSystems?.length} Systems successfully added to your Data Map`,
        { isClosable: true }
      );

      return features.plus
        ? router.push(datamapRoute.href)
        : router.push("/system");
    }
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
