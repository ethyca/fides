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
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { resolveLink } from "~/features/common/nav/zone-config";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import WarningModal from "~/features/common/WarningModal";
import { useUpsertSystemsMutation } from "~/features/system";
import { System } from "~/types/api";

import {
  changeStep,
  chooseSystemsForReview,
  selectAddSystemsMethod,
  selectSystemsForReview,
} from "./config-wizard.slice";
import { SystemMethods } from "./types";

const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Name", attribute: "name" },
  { name: "System type", attribute: "system_type" },
  { name: "Resource ID", attribute: "fidesctl_meta.resource_id" },
];

const ScanResults = () => {
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
  const method = useAppSelector(selectAddSystemsMethod);
  const { handleError } = useAPIHelper();

  const confirmRegisterSelectedSystems = async () => {
    dispatch(chooseSystemsForReview(selectedSystems.map((s) => s.fides_key)));
    const response = await upsertSystems(selectedSystems);

    if (isErrorResult(response)) {
      return handleError(response.error);
    }

    /*
     * Eventually, all scanners will go through some sort of classify flow.
     * But for now, only the data flow scanner does
     */
    if (method === SystemMethods.DATA_FLOW) {
      return router.push("/classify-systems");
    }

    const datamapRoute = resolveLink({
      href: "/datamap",
      basePath: "/",
    });

    return features.plus
      ? router.push(datamapRoute.href)
      : router.push("/system");
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

        <Box>
          <Text>
            Below are the results of your infrastructure scan. To continue,
            select the systems you would like registered in your data map and
            reports.
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

export default ScanResults;
