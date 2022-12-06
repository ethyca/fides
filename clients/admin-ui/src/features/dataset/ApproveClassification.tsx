import { Button, chakra, Spacer, useToast } from "@fidesui/react";
import { useMemo } from "react";
import { useSelector } from "react-redux";

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
        0
      ) ?? 0,
    [classifyCollection]
  );

  const handleApprove = async () => {
    if (isLoading || !(dataset && classifyDataset)) {
      return;
    }

    const updatedDataset = getUpdatedDatasetFromClassifyDataset(
      dataset,
      classifyDataset
    );
    try {
      const updateResult = await updateDataset(updatedDataset);
      if (isErrorResult(updateResult)) {
        toast(errorToastParams(getErrorMessage(updateResult.error)));
        return;
      }

      const statusResult = await updateClassifyInstance({
        dataset_fides_key: dataset.fides_key,
        status: ClassificationStatus.REVIEWED,
      });
      if (isErrorResult(statusResult)) {
        toast(errorToastParams(getErrorMessage(statusResult.error)));
        return;
      }

      toast(successToastParams("Dataset classified and approved"));
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
      <Button
        size="sm"
        variant="primary"
        flexShrink={0}
        onClick={handleApprove}
        isLoading={isLoading}
        isDisabled={isLoading}
        data-testid="approve-classification-btn"
      >
        Approve dataset classification
      </Button>
    </>
  );
};

export default ApproveClassification;
