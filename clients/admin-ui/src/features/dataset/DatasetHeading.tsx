import {
  Heading,
  HStack,
  StepperCircleCheckmarkIcon,
  Text,
  VStack,
} from "fidesui";
import { useMemo } from "react";
import { useSelector } from "react-redux";

import { selectActiveClassifyDataset } from "~/features/plus/plus.slice";
import { ClassificationStatus } from "~/types/api";

const DatasetHeading = () => {
  const classifyDataset = useSelector(selectActiveClassifyDataset);
  const status = classifyDataset?.status ?? ClassificationStatus.REVIEWED;

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
            0,
          ),
        0,
      ) ?? 0,
    [classifyDataset],
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
      {status === ClassificationStatus.COMPLETE ? (
        <>
          <HStack>
            <Heading fontSize="2xl">
              Dataset classification ready for review
            </Heading>
            <StepperCircleCheckmarkIcon fontSize="2xl" />
          </HStack>
          <Text fontSize="sm" color="gray.600" maxW="720px">
            {fieldCountMessage} For each table, please review the recommended
            data categories. You can accept the recommendation or update any
            field before approving.
          </Text>
        </>
      ) : (
        <Heading fontSize="2xl">Dataset</Heading>
      )}
    </VStack>
  );
};

export default DatasetHeading;
