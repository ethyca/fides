import {
  Center,
  GridItem,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
} from "@fidesui/react";
import { ReactNode } from "react";

import EditDrawer from "~/features/common/EditDrawer";
import { GenerateTypes, System } from "~/types/api";

import ClassificationStatusBadge from "../plus/ClassificationStatusBadge";
import {
  useGetClassifySystemQuery,
  useUpdateClassifyInstanceMutation,
} from "../plus/plus.slice";
import { useUpdateSystemMutation } from "./system.slice";

interface Props {
  system: System;
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

const useClassifySystemDrawer = ({ system }: { system: System }) => {
  const {
    data: classificationInstance,
    isLoading: isLoadingClassificationInstance,
  } = useGetClassifySystemQuery(system.fides_key);

  const hasClassification = classificationInstance != null;
  const hasIngressClassification =
    hasClassification && classificationInstance.ingress.length > 0;
  const hasEgressClassification =
    hasClassification && classificationInstance.egress.length > 0;
  const hasNoDataFlows = !hasIngressClassification && !hasEgressClassification;

  let description: JSX.Element;
  let resources: string;
  if (hasIngressClassification && hasEgressClassification) {
    resources = "ingress and egress";
  } else if (hasIngressClassification) {
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
    hasIngressClassification,
    hasEgressClassification,
    hasNoDataFlows,
    hasClassification,
    description,
    updateSystemMutation,
    updateClassificationMutation,
    classificationInstance,
    isLoadingClassificationInstance,
  };
};

const EditClassifySystemDrawer = ({ system, isOpen, onClose }: Props) => {
  const {
    description,
    isLoadingClassificationInstance,
    classificationInstance,
  } = useClassifySystemDrawer({ system });

  console.log({ classificationInstance });

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      header="System classification details"
    >
      {isLoadingClassificationInstance ? (
        <Center>
          <Spinner />
        </Center>
      ) : (
        <Stack spacing={4}>
          <SimpleGrid columns={2} spacingY={2}>
            <SystemMetadata label="System name" value={system.name} />
            <SystemMetadata label="System type" value={system.system_type} />
            <SystemMetadata
              label="Classification status"
              value={
                <ClassificationStatusBadge
                  status={classificationInstance?.status}
                  resource={GenerateTypes.SYSTEMS}
                />
              }
            />
          </SimpleGrid>

          {description}
        </Stack>
      )}
    </EditDrawer>
  );
};

export default EditClassifySystemDrawer;
