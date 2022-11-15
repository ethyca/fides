import { GridItem, SimpleGrid, Stack, Text } from "@fidesui/react";
import { ReactNode } from "react";

import EditDrawer from "~/features/common/EditDrawer";
import {
  ClassifyInstanceResponseValues,
  GenerateTypes,
  System,
} from "~/types/api";

import ClassificationStatusBadge from "../plus/ClassificationStatusBadge";
import { useUpdateClassifyInstanceMutation } from "../plus/plus.slice";
import { useUpdateSystemMutation } from "./system.slice";

interface Props {
  system: System;
  classification?: ClassifyInstanceResponseValues;
  isOpen: boolean;
  onClose: () => void;
}

const SystemMetadata = ({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) => (
  <GridItem>
    <Text as="span" fontWeight="semibold">
      {label}:
    </Text>{" "}
    {value}
  </GridItem>
);

const useClassifySystemDrawer = ({
  system,
  classification,
}: Pick<Props, "system" | "classification">) => {
  const hasIngress = system.ingress != null && system.ingress.length > 0;
  const hasEgress = system.egress != null && system.egress.length > 0;
  const hasNoDataFlows = !hasIngress && !hasEgress;
  const hasClassification = classification != null;

  let description: JSX.Element;
  let resources: string;
  if (hasIngress && hasEgress) {
    resources = "ingress and egress";
  } else if (hasIngress) {
    resources = "ingress";
  } else {
    resources = "egress";
  }
  if (hasNoDataFlows) {
    description = (
      <Text fontSize="sm" data-testid="no-data-flows">
        Fides classify did not find any ingress or egress systems connected to
        your selected system.
      </Text>
    );
  } else if (!hasClassification) {
    description = (
      <Text fontSize="sm" data-testid="no-classification">
        Fides classify has detected {resources} systems connected to your
        selected system. However, it was unable to classify the data flows based
        on a system scan. You may still manually classify the data flows.
      </Text>
    );
  } else {
    description = (
      <Text fontSize="sm" data-testid="data-flow-with-classification">
        Fides classify has detected {resources} systems connected to your
        selected system. Each system has been automatically assigned data
        categories. Choose to keep the assigned data category selection or
        review more classification recommendations.
      </Text>
    );
  }

  const [updateSystemMutation] = useUpdateSystemMutation();
  const [updateClassificationMutation] = useUpdateClassifyInstanceMutation();

  return {
    hasIngress,
    hasEgress,
    hasNoDataFlows,
    hasClassification,
    description,
    updateSystemMutation,
    updateClassificationMutation,
  };
};

const EditClassifySystemDrawer = ({
  system,
  classification,
  isOpen,
  onClose,
}: Props) => {
  const { description } = useClassifySystemDrawer({ system, classification });

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      header="System classification details"
    >
      <Stack spacing={4}>
        <SimpleGrid columns={2} spacingY={2}>
          <SystemMetadata label="System name" value={system.name} />
          <SystemMetadata label="System type" value={system.system_type} />
          <SystemMetadata
            label="Classification status"
            value={
              <ClassificationStatusBadge
                status={classification?.status}
                resource={GenerateTypes.SYSTEMS}
              />
            }
          />
        </SimpleGrid>
        {description}
      </Stack>
    </EditDrawer>
  );
};

export default EditClassifySystemDrawer;
