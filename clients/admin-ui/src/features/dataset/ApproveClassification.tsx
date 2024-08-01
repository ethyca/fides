import { Button, chakra, Spacer, useToast } from "fidesui";
import { useMemo } from "react";
import { useSelector } from "react-redux";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  selectActiveClassifyDataset,
  selectClassifyInstanceCollection,
  useUpdateClassifyInstanceMutation,
} from "~/features/plus/plus.slice";
import { ClassificationStatus } from "~/types/api";

import { selectActiveDataset, useUpdateDatasetMutation } from "./dataset.slice";
import { getUpdatedDatasetFromClassifyDataset } from "./helpers";

const ApproveClassification = () => {
  const features = useFeatures();

  const dataset = useSelector(selectActiveDataset);
  const classifyDataset = useSelector(selectActiveClassifyDataset);
  const classifyCollection = useSelector(selectClassifyInstanceCollection);

  const [updateDataset, { isLoading: datasetIsLoading }] =
    useUpdateDatasetMutation();
  const [updateClassifyInstance, { isLoading: instanceIsLoading }] =
    useUpdateClassifyInstanceMutation();
  const isLoading = datasetIsLoading || instanceIsLoading;

  const toast = useToast();

  const fieldCount = useMemo(
    () =>
      classifyCollection?.fields?.reduce(
        (acc, field) => (field.classifications.length > 0 ? acc + 1 : acc),
        0,
      ) ?? 0,
    [classifyCollection],
  );

  const handleApprove = async () => {
    if (isLoading || !(dataset && classifyDataset)) {
      return;
    }

    const updatedDataset = getUpdatedDatasetFromClassifyDataset(
      dataset,
      classifyDataset,
      features.flags.datasetClassificationUpdates
        ? classifyCollection?.name
        : undefined,
    );

    try {
      const updateResult = await updateDataset(updatedDataset);
      if (isErrorResult(updateResult)) {
        toast(errorToastParams(getErrorMessage(updateResult.error)));
        return;
      }
      if (features.flags.datasetClassificationUpdates) {
        toast(successToastParams("Collection classified and approved"));
        // Validate if any fields still require category approval
        let uncategorizedCount = 0;
        updatedDataset.collections.forEach((updatedCollection) => {
          updatedCollection.fields.forEach((updatedField) => {
            if (
              !updatedField.data_categories ||
              updatedField.data_categories.length === 0
            ) {
              uncategorizedCount += 1;
            }
          });
        });
        // Only update the dataset as classified when all fields have been categorized
        if (uncategorizedCount === 0) {
          const statusResult = await updateClassifyInstance({
            dataset_fides_key: dataset.fides_key,
            status: ClassificationStatus.REVIEWED,
          });

          if (isErrorResult(statusResult)) {
            toast(errorToastParams(getErrorMessage(statusResult.error)));
            return;
          }

          toast(successToastParams("Dataset classified and approved"));
        }
      } else {
        const statusResult = await updateClassifyInstance({
          dataset_fides_key: dataset.fides_key,
          status: ClassificationStatus.REVIEWED,
        });
        if (isErrorResult(statusResult)) {
          toast(errorToastParams(getErrorMessage(statusResult.error)));
          return;
        }
        toast(successToastParams("Dataset classified and approved"));
      }
    } catch (error) {
      toast(errorToastParams(`${error}`));
    }
  };

  // This component is only visible if the classifier has run on this dataset and has not been reviewed yet.
  if (
    !(
      classifyDataset &&
      classifyCollection &&
      classifyDataset.status === ClassificationStatus.COMPLETE
    )
  ) {
    return <Spacer />;
  }

  return (
    <>
      <chakra.p flexGrow={1} textAlign="center" fontSize="sm" color="gray.600">
        <chakra.span fontWeight="bold">{fieldCount}</chakra.span>{" "}
        {fieldCount === 1 ? "field has" : "fields have"} been identified within
        this{" "}
        <chakra.span fontWeight="bold">{classifyCollection.name}</chakra.span>{" "}
        table that are likely to contain personal data.
      </chakra.p>
      {features.flags.datasetClassificationUpdates ? (
        <Button
          size="sm"
          variant="primary"
          flexShrink={0}
          onClick={handleApprove}
          isLoading={isLoading}
          isDisabled={isLoading}
          data-testid="approve-classification-btn"
        >
          Approve classifications
        </Button>
      ) : (
        <Button
          size="sm"
          variant="primary"
          flexShrink={0}
          onClick={handleApprove}
          isLoading={isLoading}
          isDisabled={isLoading}
          data-testid="approve-classification-btn"
        >
          Approve dataset
        </Button>
      )}
    </>
  );
};

export default ApproveClassification;
