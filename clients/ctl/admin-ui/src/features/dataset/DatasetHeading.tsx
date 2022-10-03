import { Heading, HStack, Text, VStack } from "@fidesui/react";
import { useMemo } from "react";
import { useSelector } from "react-redux";

import { StepperCircleCheckmarkIcon } from "~/features/common/Icon";
import {
  ClassifyStatusEnum,
  selectActiveClassifyDataset,
} from "~/features/common/plus.slice";

const DatasetHeading = () => {
  const classifyDataset = useSelector(selectActiveClassifyDataset);
  const status = classifyDataset?.status ?? ClassifyStatusEnum.REVIEWED;

  const fieldCount = useMemo(
    () =>
      classifyDataset?.collections?.reduce(
        // Count across all collections...
        (acc, collection) =>
          acc +
          collection.fields.reduce(
            // Count the fields that have at least one classification.
            (fieldAcc, field) =>
              field.classifications.length > 0 ? fieldAcc + 1 : fieldAcc,
            0
          ),
        0
      ) ?? 0,
    [classifyDataset]
  );

  /* eslint-disable no-nested-ternary */
  const fieldCountMessage =
    fieldCount === 0
      ? "Fides did not identify any fields that are likely to contain personal data, but there may be some."
      : fieldCount === 1
      ? "Fides identified a field that is likely to contain personal data."
      : `Fides identified ${fieldCount} fields that are likely to contain personal data.`;

  return (
    <VStack align="left" mb={6}>
      {status === ClassifyStatusEnum.COMPLETE ? (
        <>
          <HStack>
            <Heading fontSize="2xl">
              Dataset classification ready for review
            </Heading>
            <StepperCircleCheckmarkIcon fontSize="2xl" />
          </HStack>
          <Text fontSize="sm" color="gray.600" maxW="720px">
            {fieldCountMessage} Please confirm all dataset fields to finish
            annotating this system. For each table, please review the
            recommended data categories. You can accept the automated
            suggestions, or update any field as appropriate before approving.
          </Text>
        </>
      ) : (
        <Heading fontSize="2xl">Dataset</Heading>
      )}
    </VStack>
  );
};

export default DatasetHeading;
