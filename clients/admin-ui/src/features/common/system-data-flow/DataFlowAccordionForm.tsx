import {
  Button,
  Collapse,
  CollapseProps,
  Flex,
  Icons,
  Space,
  Tag,
  Text,
  useMessage,
} from "fidesui";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { isErrorResult } from "~/features/common/helpers";
import {
  registerForm,
  unregisterForm,
  updateDirtyFormState,
} from "~/features/common/hooks/dirty-forms.slice";
import { DataFlowSystemsDeleteTable } from "~/features/common/system-data-flow/DataFlowSystemsDeleteTable";
import DataFlowSystemsModal from "~/features/common/system-data-flow/DataFlowSystemsModal";
import {
  useGetAllSystemsQuery,
  useUpdateSystemMutation,
} from "~/features/system";
import { DataFlow, System } from "~/types/api";

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
  const message = useMessage();
  const dispatch = useAppDispatch();
  const flowType = isIngress ? "Source" : "Destination";
  const pluralFlowType = `${flowType}s`;
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  const [assignedDataFlows, setAssignedDataFlows] =
    useState<DataFlow[]>(initialDataFlows);

  useEffect(() => {
    setAssignedDataFlows(initialDataFlows);
  }, [initialDataFlows]);

  const isDirty = assignedDataFlows !== initialDataFlows;

  // FormGuard: register/unregister form and track dirty state via Redux
  const formId = `${system.fides_key}:${flowType}`;
  useEffect(() => {
    dispatch(registerForm({ id: formId, name: `${flowType} Data Flow` }));
    return () => {
      dispatch(unregisterForm({ id: formId }));
    };
  }, [dispatch, formId, flowType]);

  useEffect(() => {
    dispatch(updateDirtyFormState({ id: formId, isDirty }));
  }, [isDirty, dispatch, formId]);

  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true);
    const updatedSystem = {
      ...system,
      ingress: isIngress ? assignedDataFlows : system.ingress,
      egress: !isIngress ? assignedDataFlows : system.egress,
    };
    const result = await updateSystemMutationTrigger(updatedSystem);

    if (isErrorResult(result)) {
      message.error("Failed to update data flows");
    } else {
      message.success(`${pluralFlowType} updated`);
    }
    setIsSubmitting(false);
  }, [
    system,
    isIngress,
    assignedDataFlows,
    updateSystemMutationTrigger,
    message,
    pluralFlowType,
  ]);

  const handleCancel = useCallback(() => {
    setAssignedDataFlows(initialDataFlows);
  }, [initialDataFlows]);

  const handleDelete = useCallback((systemToDelete: System) => {
    setAssignedDataFlows((prev) =>
      prev.filter((df) => df.fides_key !== systemToDelete.fides_key),
    );
  }, []);

  const collapseItems: CollapseProps["items"] = useMemo(
    () => [
      {
        key: flowType,
        label: (
          <Flex
            align="center"
            gap="small"
            className={isSystemTab ? "pl-4" : undefined}
            data-testid={`data-flow-button-${flowType}`}
          >
            <Text strong size="sm">
              {pluralFlowType}
            </Text>
            <Tag color="info">{assignedDataFlows.length}</Tag>
          </Flex>
        ),
        children: (
          <Space
            direction="vertical"
            size="middle"
            className="w-full"
            data-testid={`data-flow-panel-${flowType}`}
          >
            <Button
              onClick={() => setModalOpen(true)}
              type="primary"
              size="small"
              icon={<Icons.Settings />}
              iconPlacement="end"
              className="mb-4"
              data-testid="assign-systems-btn"
            >
              {`Configure ${pluralFlowType.toLocaleLowerCase()}`}
            </Button>
            <DataFlowSystemsDeleteTable
              systems={systems}
              dataFlows={assignedDataFlows}
              onDelete={handleDelete}
            />

            <Flex gap={2} className="mt-6">
              <Button
                disabled={!isDirty}
                onClick={handleCancel}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                type="primary"
                onClick={handleSubmit}
                loading={isSubmitting}
                disabled={!isDirty}
                data-testid="save-btn"
              >
                Save
              </Button>
            </Flex>
            {/* By conditionally rendering the modal, we force it to reset its state
            whenever it opens */}
            {modalOpen ? (
              <DataFlowSystemsModal
                currentSystem={system}
                systems={systems}
                isOpen={modalOpen}
                onClose={() => setModalOpen(false)}
                dataFlowSystems={assignedDataFlows}
                onDataFlowSystemChange={setAssignedDataFlows}
                flowType={flowType}
              />
            ) : null}
          </Space>
        ),
      },
    ],
    [
      flowType,
      isSystemTab,
      pluralFlowType,
      assignedDataFlows,
      systems,
      handleDelete,
      isDirty,
      handleCancel,
      handleSubmit,
      isSubmitting,
      modalOpen,
      system,
    ],
  );

  return (
    <Collapse
      items={collapseItems}
      data-testid={`data-flow-collapse-${flowType}`}
    />
  );
};
