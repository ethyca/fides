import { Button, chakra, HStack } from "@fidesui/react";
import { useMemo } from "react";
import { useSelector } from "react-redux";

import {
  ClassifyStatusEnum,
  selectActiveClassifyDataset,
  selectClassifyInstanceCollection,
} from "~/features/common/plus.slice";

const ApproveClassification = () => {
  const classifyDataset = useSelector(selectActiveClassifyDataset);
  const classifyCollection = useSelector(selectClassifyInstanceCollection);

  const fieldCount = useMemo(
    () =>
      classifyCollection?.fields?.reduce(
        (acc, field) => (field.classifications.length > 0 ? acc + 1 : acc),
        0
      ) ?? 0,
    [classifyCollection]
  );

  const handleApprove = () => {};

  // This component is only visible if the classifier has run on this dataset and has not been reviewed yet.
  if (
    !(
      classifyDataset &&
      classifyCollection &&
      classifyDataset.status === ClassifyStatusEnum.COMPLETE
    )
  ) {
    return null;
  }

  return (
    <HStack>
      <chakra.p fontSize="sm" color="gray.600">
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
      >
        Approve dataset classification
      </Button>
    </HStack>
  );
};

export default ApproveClassification;
