import {
  Center,
  GridItem,
  SimpleGrid,
  Spinner,
  Stack,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { narrow } from "narrow-minded";
import { ReactNode } from "react";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import ClassificationStatusBadge from "~/features/plus/ClassificationStatusBadge";
import {
  useGetClassifySystemQuery,
  useUpdateClassifyInstanceMutation,
} from "~/features/plus/plus.slice";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";
import {
  ClassificationStatus,
  ClassifyEmpty,
  ClassifySystem,
  GenerateTypes,
  System,
} from "~/types/api";

import DataFlowsAccordion, { IngressEgress } from "./DataFlowsAccordion";
import { useUpdateSystemMutation } from "./system.slice";

const FORM_ID = "data-flow-form";

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

const isClassifySystem = (
  payload: ClassifyEmpty | ClassifySystem | undefined,
): payload is ClassifySystem => narrow({ fides_key: "string" }, payload);

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

  let description: JSX.Element;
  if (
    classificationInstance != null &&
    !isClassifySystem(classificationInstance)
  ) {
    description = (
      <Text fontSize="sm" data-testid="no-classification-instance">
        No classification instance found but you may still manually classify the
        data flows.
      </Text>
    );
  } else {
    const systemIngresses = system.ingress || [];
    const systemEgresses = system.egress || [];

    // Classification can return some data flows that don't exist on the system object.
    // We should only show the ones that do exist on the system
    const classifiedIngresses =
      classificationInstance?.ingress.filter((i) =>
        systemIngresses.find((si) => si.fides_key === i.fides_key),
      ) || [];
    const classifiedEgresses =
      classificationInstance?.egress.filter((e) =>
        systemEgresses.find((se) => se.fides_key === e.fides_key),
      ) || [];

    const hasIngressClassification = classifiedIngresses.length > 0;
    const hasEgressClassification = classifiedEgresses.length > 0;
    const hasNoDataFlowClassifications =
      !hasIngressClassification && !hasEgressClassification;

    const hasIngress = systemIngresses.length > 0;
    const hasEgress = systemEgresses.length > 0;
    const hasNoDataFlows = !hasIngress && !hasEgress;

    let dataFlowDescription: string;
    if (hasIngress && hasEgress) {
      dataFlowDescription =
        "which send or receive data from your selected system";
    } else if (hasIngress) {
      dataFlowDescription = "from which your selected system receives data";
    } else {
      dataFlowDescription = "to which your selected system sends data";
    }
    if (classificationInstance?.status === ClassificationStatus.PROCESSING) {
      description = (
        <Text fontSize="sm" data-testid="processing">
          Fides classify is still classifying, please check back later.
        </Text>
      );
    } else if (hasNoDataFlows) {
      description = (
        <Text fontSize="sm" data-testid="no-data-flows">
          Fides classify did not detect any additional systems sending or
          receiving data from your selected system.
        </Text>
      );
    } else if (hasNoDataFlowClassifications) {
      description = (
        <Text fontSize="sm" data-testid="no-classification">
          Fides classify has detected additional systems which send or receive
          data from your selected system, but was unable to classify these data
          flows. You may classify these data flows manually below.
        </Text>
      );
    } else {
      description = (
        <Text fontSize="sm" data-testid="data-flow-with-classification">
          Fides classify has detected additional systems {dataFlowDescription}.
          Each system has been automatically assigned data categories. Choose to
          keep the assigned data category selection or review more
          classification recommendations.
        </Text>
      );
    }
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
    description,
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

  const handleUpdateSystem = async ({ ingress, egress }: IngressEgress) => {
    await handleSave({ ...system, ingress, egress });
  };

  const initialValues = {
    egress: system.egress ?? [],
    ingress: system.ingress ?? [],
  };

  const status = isClassifySystem(classificationInstance)
    ? classificationInstance.status
    : undefined;
  const showDataFlowsAccordion = status !== ClassificationStatus.PROCESSING;

  return (
    <Formik initialValues={initialValues} onSubmit={handleUpdateSystem}>
      {({ isSubmitting }) => (
        <Form id={FORM_ID}>
          <EditDrawer
            isOpen={isOpen}
            onClose={onClose}
            header={<EditDrawerHeader title="System classification details" />}
            footer={
              status !== ClassificationStatus.PROCESSING ? (
                <EditDrawerFooter
                  onClose={onClose}
                  formId={FORM_ID}
                  isSaving={isSubmitting}
                />
              ) : undefined
            }
          >
            {isLoadingClassificationInstance ? (
              <Center>
                <Spinner />
              </Center>
            ) : (
              <Stack spacing={4}>
                <SimpleGrid columns={2} spacingY={2}>
                  <SystemMetadata label="System name" value={system.name} />
                  <SystemMetadata
                    label="System type"
                    value={system.system_type}
                  />
                  <SystemMetadata
                    label="Classification status"
                    value={
                      <ClassificationStatusBadge
                        status={status}
                        resource={GenerateTypes.SYSTEMS}
                        display="inline"
                      />
                    }
                  />
                </SimpleGrid>

                {description}
                {showDataFlowsAccordion ? (
                  <DataFlowsAccordion
                    system={system}
                    classificationInstance={
                      isClassifySystem(classificationInstance)
                        ? classificationInstance
                        : undefined
                    }
                  />
                ) : null}
              </Stack>
            )}
          </EditDrawer>
        </Form>
      )}
    </Formik>
  );
};

export default EditClassifySystemDrawer;
