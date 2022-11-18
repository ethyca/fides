import {
  Center,
  GridItem,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { ReactNode } from "react";

import EditDrawer from "~/features/common/EditDrawer";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import ClassificationStatusBadge from "~/features/plus/ClassificationStatusBadge";
import {
  useGetClassifySystemQuery,
  useUpdateClassifyInstanceMutation,
} from "~/features/plus/plus.slice";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";
import { ClassificationStatus, GenerateTypes, System } from "~/types/api";

import DataFlowForm, { FORM_ID, IngressEgress } from "./DataFlowForm";
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

const useClassifySystemDrawer = ({
  system,
  onClose,
}: {
  system: System;
  onClose: () => void;
}) => {
  const toast = useToast();

  // Subscriptions
  useGetAllDataCategoriesQuery();
  const {
    data: classificationInstance,
    isLoading: isLoadingClassificationInstance,
  } = useGetClassifySystemQuery(system.fides_key);

  const systemIngresses = system.ingress || [];
  const systemEgresses = system.egress || [];

  // Classification can return some data flows that don't exist on the system object.
  // We should only show the ones that do exist on the system
  const classifiedIngresses =
    classificationInstance?.ingress.filter((i) =>
      systemIngresses.find((si) => si.fides_key === i.fides_key)
    ) || [];
  const classifiedEgresses =
    classificationInstance?.egress.filter((e) =>
      systemEgresses.find((se) => se.fides_key === e.fides_key)
    ) || [];

  const hasIngressClassification = classifiedIngresses.length > 0;
  const hasEgressClassification = classifiedEgresses.length > 0;
  const hasNoDataFlowClassifications =
    !hasIngressClassification && !hasEgressClassification;

  const hasIngress = systemIngresses.length > 0;
  const hasEgress = systemEgresses.length > 0;
  const hasNoDataFlows = !hasIngress && !hasEgress;

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
  } else if (hasNoDataFlowClassifications) {
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

  const handleSave = async (updatedSystem: System) => {
    if (isLoadingClassificationInstance || !classificationInstance) {
      return;
    }

    try {
      const updateResult = await updateSystemMutation(updatedSystem);
      if (isErrorResult(updateResult)) {
        toast(errorToastParams(getErrorMessage(updateResult.error)));
        return;
      }

      const statusResult = await updateClassificationMutation({
        dataset_fides_key: updatedSystem.fides_key,
        status: ClassificationStatus.REVIEWED,
        resource_type: GenerateTypes.SYSTEMS,
      });
      if (isErrorResult(statusResult)) {
        toast(errorToastParams(getErrorMessage(statusResult.error)));
        return;
      }

      toast(successToastParams("System data flows classified and approved"));
      onClose();
    } catch (error) {
      toast(errorToastParams(`${error}`));
    }
  };

  return {
    hasIngressClassification,
    hasEgressClassification,
    hasNoDataFlows,
    description,
    updateSystemMutation,
    updateClassificationMutation,
    classificationInstance,
    isLoadingClassificationInstance,
    handleSave,
  };
};

const EditClassifySystemDrawer = ({ system, isOpen, onClose }: Props) => {
  const {
    description,
    isLoadingClassificationInstance,
    classificationInstance,
    handleSave,
  } = useClassifySystemDrawer({ system, onClose });

  const handleUpdateSystem = ({ ingress, egress }: IngressEgress) => {
    handleSave({ ...system, ingress, egress });
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      header="System classification details"
      formId={FORM_ID}
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
                  display="inline"
                />
              }
            />
          </SimpleGrid>

          {description}
          <DataFlowForm
            system={system}
            onSave={handleUpdateSystem}
            classificationInstance={classificationInstance}
          />
        </Stack>
      )}
    </EditDrawer>
  );
};

export default EditClassifySystemDrawer;
