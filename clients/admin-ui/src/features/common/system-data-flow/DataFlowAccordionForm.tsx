import { DataFlow, RoleRegistryEnum, System } from "~/types/api";
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
import {
  useGetAllSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system";
import QuestionTooltip from "common/QuestionTooltip";
import { DataFlowSystemsDeleteTable } from "common/system-data-flow/DataFlowSystemsDeleteTable";
import DataFlowSystemsModal from "common/system-data-flow/DataFlowSystemsModal";
import React, { useState, useMemo, useEffect } from "react";
import { Formik, Form } from "formik";

import { GearLightIcon } from "common/Icon";
import { successToastParams } from "common/toast";

const defaultInitialValues = {
  dataFlowSystems: [] as DataFlow[],
};

export type FormValues = typeof defaultInitialValues;

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  system: System;
};

export const DataFlowAccordionForm = ({
  system,
  isIngress,
}: DataFlowAccordionItemProps) => {
  const toast = useToast();
  const flowType = isIngress ? "Source" : "Destination";
  const pluralFlowType = `${flowType}s`;
  const dataFlowSystemsModal = useDisclosure();
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();

  const { data } = useGetAllSystemsQuery();
  const systems = data || [];

  const initialDataFlows = useMemo(() => {
    const dataFlows = isIngress ? system.ingress! : system.egress!;
    const systemFidesKeys = systems ? systems.map((s) => s.fides_key) : [];

    return dataFlows.filter((df) => systemFidesKeys.includes(df.fides_key));
  }, [isIngress, system, systems]);

  const [assignedDataFlow, setAssignedDataFlows] =
    useState<DataFlow[]>(initialDataFlows);

  useEffect(() => {
    setAssignedDataFlows(initialDataFlows);
  }, [initialDataFlows]);
  const handleSubmit = async ({ dataFlowSystems }: FormValues) => {
    const updatedSystem = {
      ...system,
      ingress: isIngress ? dataFlowSystems : system.ingress,
      egress: !isIngress ? dataFlowSystems : system.egress,
    };
    await updateSystemMutationTrigger(updatedSystem);
    toast(successToastParams(`${pluralFlowType} updated`));
  };

  return (
    <AccordionItem>
      <AccordionButton height="44px" padding={2}>
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
      <AccordionPanel backgroundColor="gray.50" padding={6}>
        <Stack
          borderRadius="md"
          backgroundColor="gray.50"
          aria-selected="true"
          spacing={4}
          data-testid="selected"
        >
          <Formik initialValues={defaultInitialValues} onSubmit={handleSubmit}>
            {({ values, isSubmitting, dirty, resetForm }) => (
              <Form>
                <Button
                  colorScheme="primary"
                  size="xs"
                  width="fit-content"
                  onClick={dataFlowSystemsModal.onOpen}
                  data-testid="assign-systems-btn"
                  rightIcon={<GearLightIcon />}
                >
                  {`Configure ${pluralFlowType}`}
                </Button>
                <DataFlowSystemsDeleteTable
                  currentSystem={system}
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
