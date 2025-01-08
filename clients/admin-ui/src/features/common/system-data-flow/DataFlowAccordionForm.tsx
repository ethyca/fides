import { isErrorResult } from "common/helpers";
import { FormGuard } from "common/hooks/useIsAnyFormDirty";
import { GearLightIcon } from "common/Icon";
import { DataFlowSystemsDeleteTable } from "common/system-data-flow/DataFlowSystemsDeleteTable";
import DataFlowSystemsModal from "common/system-data-flow/DataFlowSystemsModal";
import { errorToastParams, successToastParams } from "common/toast";
import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  AntButton as Button,
  Flex,
  Spacer,
  Stack,
  Tag,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import React, { useEffect, useMemo, useState } from "react";

import {
  useGetAllSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system";
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
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();

  const { data: systems = [] } = useGetAllSystemsQuery();

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
    { resetForm }: FormikHelpers<FormValues>,
  ) => {
    const updatedSystem = {
      ...system,
      ingress: isIngress ? dataFlowSystems : system.ingress,
      egress: !isIngress ? dataFlowSystems : system.egress,
    };
    const result = await updateSystemMutationTrigger(updatedSystem);

    if (isErrorResult(result)) {
      toast(errorToastParams("Failed to update data flows"));
    } else {
      toast(successToastParams(`${pluralFlowType} updated`));
    }

    resetForm({ values: { dataFlowSystems } });
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
          <Text fontSize="sm" lineHeight={5} fontWeight="semibold" mr={2}>
            {pluralFlowType}
          </Text>
          {/* Commented out until we get copy for the tooltips */}
          {/* <QuestionTooltip label="helpful tip" /> */}

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
                  onClick={dataFlowSystemsModal.onOpen}
                  type="primary"
                  size="small"
                  icon={<GearLightIcon />}
                  iconPosition="end"
                  className="mb-4"
                  data-testid="assign-systems-btn"
                >
                  {`Configure ${pluralFlowType.toLocaleLowerCase()}`}
                </Button>
                <DataFlowSystemsDeleteTable
                  systems={systems}
                  dataFlows={assignedDataFlow}
                  onDataFlowSystemChange={setAssignedDataFlows}
                />

                <div className="mt-6 flex gap-2">
                  <Button
                    disabled={!dirty && assignedDataFlow === initialDataFlows}
                    onClick={() => {
                      setAssignedDataFlows(initialDataFlows);
                      resetForm({
                        values: { dataFlowSystems: initialDataFlows },
                      });
                    }}
                    data-testid="cancel-btn"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={isSubmitting}
                    disabled={!dirty && assignedDataFlow === initialDataFlows}
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </div>
                {/* By conditionally rendering the modal, we force it to reset its state
                whenever it opens */}
                {dataFlowSystemsModal.isOpen ? (
                  <DataFlowSystemsModal
                    currentSystem={system}
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
