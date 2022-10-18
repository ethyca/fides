import { WarningIcon } from "@chakra-ui/icons";
import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Box,
  Button,
  Checkbox,
  Heading,
  HStack,
  Stack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useDisclosure,
} from "@fidesui/react";
import { Field, FieldProps, Form, Formik } from "formik";
import React, { useMemo, useRef, useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import {
  changeStep,
  chooseSystemsForReview,
  selectSystemsForReview,
} from "./config-wizard.slice";

interface FormValues {
  selectedKeys: string[];
}

const ValidationSchema = Yup.object().shape({
  selectedKeys: Yup.array()
    .of(Yup.string())
    .compact()
    .required()
    .min(1)
    .label("Selected systems"),
});

const ScanResultsForm = () => {
  const systems = useAppSelector(selectSystemsForReview);
  const dispatch = useAppDispatch();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const cancelRef = useRef(null);
  const [selectedKeyValues, setSelectedKeyValues] = useState<string[]>([]);

  const initialValues: FormValues = useMemo(
    () => ({
      selectedKeys: systems.map((s) => s.fides_key),
    }),
    [systems]
  );

  const handleSubmit = (values: FormValues) => {
    if (systems.length > values.selectedKeys.length) {
      setSelectedKeyValues(values.selectedKeys);
      onOpen();
    } else {
      dispatch(chooseSystemsForReview(values.selectedKeys));
      dispatch(changeStep());
    }
  };

  const confirmRegisterSelectedSystems = () => {
    dispatch(chooseSystemsForReview(selectedKeyValues));
    dispatch(changeStep());
  };

  const handleCancel = () => {
    dispatch(changeStep(2));
  };

  // TODO: Store the region the user submitted through the form.
  const region = "the specified region";

  return (
    <Box maxW="full">
      <AlertDialog
        isOpen={isOpen}
        leastDestructiveRef={cancelRef}
        onClose={onClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent alignItems="center" textAlign="center">
            <WarningIcon marginTop={3} />
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Warning
            </AlertDialogHeader>

            <AlertDialogBody pt={0}>
              <Text color="gray.500" mb={3}>
                You’re registering {selectedKeyValues.length} of{" "}
                {systems.length} systems available. Do you want to continue with
                registration or cancel and register all systems now?
              </Text>
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button
                ref={cancelRef}
                onClick={onClose}
                ml={3}
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                colorScheme="primary"
                onClick={() => confirmRegisterSelectedSystems()}
                variant="outline"
              >
                Continue
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
      <Formik
        initialValues={initialValues}
        validationSchema={ValidationSchema}
        onSubmit={handleSubmit}
      >
        {({ isValid, values, setValues }) => {
          const handleChangeAll = (
            event: React.ChangeEvent<HTMLInputElement>
          ) => {
            if (event.target.checked) {
              setValues(initialValues);
            } else {
              setValues({ selectedKeys: [] });
            }
          };

          const allChecked =
            values.selectedKeys.length === initialValues.selectedKeys.length;

          return (
            <Form data-testid="scan-results-form">
              <Stack spacing={10}>
                <Heading as="h3" size="lg">
                  Scan results
                </Heading>

                <Text>
                  Below are search results for {region}. Please select and
                  register the systems you would like to maintain in your
                  mapping and reports.
                </Text>

                {/* TODO(#879): Build out the SystemsTable to have a reusable view for selecting
                    systems, searching by column, etc.
                */}
                <TableContainer>
                  <Table>
                    <Thead>
                      <Tr>
                        <Th>
                          <Checkbox
                            title="Select All"
                            isChecked={allChecked}
                            onChange={handleChangeAll}
                          />
                        </Th>
                        <Th>SYSTEM NAME</Th>
                        <Th>SYSTEM TYPE</Th>
                        <Th>RESOURCE ID</Th>

                        {/* TODO(#876): These fields are not yet returned by the API.
                          <Th>REGION/ZONE</Th>
                          <Th>INSTANCE NAME</Th>
                          <Th>RESOURCE GROUP</Th>
                        */}
                      </Tr>
                    </Thead>
                    <Tbody>
                      {systems.map((system) => (
                        <Tr key={system.fides_key}>
                          <Td>
                            <Field
                              type="checkbox"
                              name="selectedKeys"
                              value={system.fides_key}
                            >
                              {({ field }: FieldProps<string>) => (
                                <Checkbox
                                  {...field}
                                  isChecked={field.checked}
                                />
                              )}
                            </Field>
                          </Td>
                          <Td>
                            <label htmlFor={`checkbox-${system.fides_key}`}>
                              {system.name}
                            </label>
                          </Td>
                          <Td>{system.system_type}</Td>
                          <Td>
                            <Box
                              maxW="200px"
                              overflow="hidden"
                              textOverflow="ellipsis"
                              title={system.fidesctl_meta?.resource_id}
                            >
                              {system.fidesctl_meta?.resource_id}
                            </Box>
                          </Td>

                          {/* TODO(#876): These fields are not yet returned by the API.
                            <Td>{system.fidesctl_meta?.region_name}</Td>
                            <Td>{system.fidesctl_meta?.instance_name}</Td>
                            <Td>{system.fidesctl_meta?.resource_group}</Td>
                          */}
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </TableContainer>

                <HStack>
                  <Button variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" isDisabled={!isValid}>
                    Register selected systems
                  </Button>
                </HStack>
              </Stack>
            </Form>
          );
        }}
      </Formik>
    </Box>
  );
};

export default ScanResultsForm;
