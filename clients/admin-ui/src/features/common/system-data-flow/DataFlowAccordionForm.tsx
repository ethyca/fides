import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Button,
  ButtonGroup,
  Flex,
  Spacer,
  Stack,
  Tag,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { FormGuard } from "common/hooks/useIsAnyFormDirty";
import { GearLightIcon } from "common/Icon";
import QuestionTooltip from "common/QuestionTooltip";
import { DataFlowSystemsDeleteTable } from "common/system-data-flow/DataFlowSystemsDeleteTable";
import DataFlowSystemsModal from "common/system-data-flow/DataFlowSystemsModal";
import { errorToastParams,successToastParams } from "common/toast";
import { Form, Formik, FormikBag } from "formik";
import React, { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  useGetAllSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system";
import { selectAllSystems } from "~/features/system/system.slice";
import { DataFlow, System } from "~/types/api";

const defaultInitialValues = {
  dataFlowSystems: [] as DataFlow[],
};

export type FormValues = typeof defaultInitialValues;

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  system: System;
  isSystemTab?: boolean;
};

export const DataFlowAccordionForm = ({
  system,
  isIngress,
  isSystemTab,
}: DataFlowAccordionItemProps) => {
  const toast = useToast();
  const flowType = isIngress ? "Source" : "Destination";
  const pluralFlowType = `${flowType}s`;
  const dataFlowSystemsModal = useDisclosure();
  const [updateSystemMutationTrigger, mutationResult] =
    useUpdateSystemMutation();

  useEffect(() => {
    if (mutationResult.isLoading || mutationResult.isUninitialized) {
      return;
    }

    if (mutationResult.isError) {
      toast(errorToastParams("Failed to update data flows"));
    }
    if (mutationResult.isSuccess) {
      toast(successToastParams(`${pluralFlowType} updated`));
    }
  }, [
    mutationResult.error,
    mutationResult.isError,
    mutationResult.isLoading,
    mutationResult.isSuccess,
    mutationResult.isUninitialized,
    pluralFlowType,
    toast,
  ]);

  useGetAllSystemsQuery();
  const systems = useAppSelector(selectAllSystems);

  const initialDataFlows = useMemo(() => {
    let dataFlows = isIngress ? system.ingress : system.egress;
    if (!dataFlows) {
      dataFlows = [];
    }
    const systemFidesKeys = systems ? systems.map((s) => s.fides_key) : [];

    return dataFlows.filter((df) => systemFidesKeys.includes(df.fides_key));
  }, [isIngress, system, systems]);

  const [assignedDataFlow, setAssignedDataFlows] =
    useState<DataFlow[]>(initialDataFlows);

  useEffect(() => {
    setAssignedDataFlows(initialDataFlows);
  }, [initialDataFlows]);

  const handleSubmit = async (
    { dataFlowSystems }: FormValues,
    { resetForm }: FormikBag<any, any>
  ) => {
    const updatedSystem = {
      ...system,
      ingress: isIngress ? dataFlowSystems : system.ingress,
      egress: !isIngress ? dataFlowSystems : system.egress,
    };
    await updateSystemMutationTrigger(updatedSystem);
    resetForm(dataFlowSystems);
  };

  return (
    <AccordionItem>
      <AccordionButton
        height="68px"
        paddingLeft={isSystemTab ? 6 : 2}
        data-testid={`data-flow-button-${flowType}`}
      >
        <Flex
          alignItems="center"
          justifyContent="start"
          flex={1}
          textAlign="left"
        >
          <Text fontSize="sm" lineHeight={5} fontWeight="semibold" mr={4}>
            {pluralFlowType}
          </Text>
          <QuestionTooltip label="helpful tip" />

          <Tag
            ml={2}
            backgroundColor="primary.400"
            borderRadius="6px"
            color="white"
          >
            {assignedDataFlow.length}
          </Tag>
          <Spacer />
          <AccordionIcon />
        </Flex>
      </AccordionButton>
      <AccordionPanel
        backgroundColor="gray.50"
        padding={6}
        data-testid={`data-flow-panel-${flowType}`}
      >
        <Stack
          borderRadius="md"
          backgroundColor="gray.50"
          aria-selected="true"
          spacing={4}
          data-testid="selected"
        >
          <Formik initialValues={defaultInitialValues} onSubmit={handleSubmit}>
            {({ isSubmitting, dirty, resetForm }) => (
              <Form>
                <FormGuard
                  id={`${system.fides_key}:${flowType}`}
                  name={`${flowType} Data Flow`}
                />
                <Button
                  colorScheme="primary"
                  size="xs"
                  width="fit-content"
                  onClick={dataFlowSystemsModal.onOpen}
                  data-testid="assign-systems-btn"
                  rightIcon={<GearLightIcon />}
                  marginBottom={4}
                >
                  {`Configure ${pluralFlowType}`}
                </Button>
                <DataFlowSystemsDeleteTable
                  systems={systems}
                  dataFlows={assignedDataFlow}
                  onDataFlowSystemChange={setAssignedDataFlows}
                />

                <ButtonGroup marginTop={6}>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!dirty && assignedDataFlow === initialDataFlows}
                    onClick={() => {
                      setAssignedDataFlows(initialDataFlows);
                      resetForm({
                        values: { dataFlowSystems: initialDataFlows },
                      });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="primary"
                    type="submit"
                    isLoading={isSubmitting}
                    disabled={!dirty && assignedDataFlow === initialDataFlows}
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </ButtonGroup>
                {/* By conditionally rendering the modal, we force it to reset its state
                whenever it opens */}
                {dataFlowSystemsModal.isOpen ? (
                  <DataFlowSystemsModal
                    systems={systems}
                    isOpen={dataFlowSystemsModal.isOpen}
                    onClose={dataFlowSystemsModal.onClose}
                    dataFlowSystems={assignedDataFlow}
                    onDataFlowSystemChange={setAssignedDataFlows}
                    flowType={flowType}
                  />
                ) : null}
              </Form>
            )}
          </Formik>
        </Stack>
      </AccordionPanel>
    </AccordionItem>
  );
};
