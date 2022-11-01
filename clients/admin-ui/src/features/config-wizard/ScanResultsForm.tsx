import {
  Box,
  Button,
  Heading,
  HStack,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { Field, FieldProps, Form, Formik } from "formik";
import { useRouter } from "next/router";
import React, { useMemo, useState } from "react";
import * as Yup from "yup";

import {
  ColumnDropdown,
  ColumnMetadata,
} from "~/features/common/ColumnDropdown";
import { SystemsCheckboxTable } from "~/features/common/SystemsCheckboxTable";
import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { defaultInitialValues } from "~/features/system/form";

import { useFeatures } from "../common/features.slice";
import WarningModal from "../common/WarningModal";
import { useCreateSystemMutation } from "../system";
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
  const [selectedKeyValues, setSelectedKeyValues] = useState<string[]>([]);
  const [createSystem] = useCreateSystemMutation();
const [selectedSystems, setSelectedSystems] = useState<System[]>(systems);
  const features = useFeatures();
  const [selectedColumns, setSelectedColumns] =
    useState<ColumnMetadata[]>(ALL_COLUMNS);

  const confirmRegisterSelectedSystems = () => {
    dispatch(chooseSystemsForReview(selectedSystems.map((s) => s.fides_key)));
    dispatch(changeStep());
  };

  const createSystems = async (values: FormValues) => {
    const systemBodyArray = values.selectedKeys.map((val) => ({
      ...defaultInitialValues,
      fides_key: val,
      // to post systems without the declaration steps, they need to at least have default values, including
      // a valid link in the data protection impact assessment
      data_protection_impact_assessment: { link: "http://www.ethyca.com" },
    }));

    await systemBodyArray.forEach(async (system) => createSystem(system));
  };

  /* const handleSubmit = (values: FormValues) => {
    if (systems.length > values.selectedKeys.length) {
      setSelectedKeyValues(values.selectedKeys);
      onOpen();
    }

    // manual system setup will go to privacy declaration step
    if (
      systems.length <= values.selectedKeys.length &&
      manualSystemSetupChosen
    ) {
      dispatch(chooseSystemsForReview(values.selectedKeys));
      dispatch(changeStep()); */

  const handleSubmit = () => {
    if (systems.length > selectedSystems.length) {
      onWarningOpen();
    } else {
      confirmRegisterSelectedSystems();
    }

    // non-plus and non-manual system setup will go to system page
    /* if (
      !features.plus &&
      systems.length <= values.selectedKeys.length &&
      !manualSystemSetupChosen
    ) {
      createSystems(values);
      router.push(`/system`);
    }

    // plus and non-manual system setup will go to datamap page
    if (
      features.plus &&
      systems.length <= values.selectedKeys.length &&
      !manualSystemSetupChosen
    ) {
      createSystems(values);
      router.push(`/datamap`);
    }
  }; */

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
