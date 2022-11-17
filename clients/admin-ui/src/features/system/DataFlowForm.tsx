import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik, useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import ClassifiedDataCategoryDropdown from "~/features/dataset/ClassifiedDataCategoryDropdown";
import {
  selectDataCategories,
  selectDataCategoriesMap,
} from "~/features/taxonomy";
import {
  ClassifyDataFlow,
  ClassifySystem,
  DataFlow,
  System,
} from "~/types/api";

export interface IngressEgress {
  ingress: DataFlow[];
  egress: DataFlow[];
}

const AccordionItemContents = ({
  headingLevel,
  title,
  children,
}: {
  headingLevel: "h2" | "h3";
  title: string;
  children: ReactNode;
}) => (
  <>
    <Heading as={headingLevel}>
      <AccordionButton
        _expanded={{ color: "complimentary.500" }}
        _hover={{ bg: "gray.50" }}
        pl={0}
      >
        <Box flex="1" textAlign="left">
          {title}
        </Box>
        <AccordionIcon />
      </AccordionButton>
    </Heading>
    <AccordionPanel py={2} px={0}>
      {children}
    </AccordionPanel>
  </>
);

const DataFlows = ({
  classifyDataFlows,
  type,
}: {
  classifyDataFlows?: ClassifyDataFlow[];
  type: "ingress" | "egress";
}) => {
  const { values, setFieldValue } = useFormikContext<IngressEgress>();
  const flows = values[type];

  const dataCategories = useAppSelector(selectDataCategories);
  const dataCategoriesMap = useAppSelector(selectDataCategoriesMap);

  if (flows.length === 0) {
    return <Text p={4}>No {type}es found.</Text>;
  }

  return (
    <AccordionItem p={0} data-testid={`accordion-item-${type}`}>
      <AccordionItemContents
        headingLevel="h2"
        title={`Connected ${
          type[0].toLocaleUpperCase() + type.slice(1)
        } Systems`}
      >
        {flows.map((flow, idx) => {
          const handleChecked = (newChecked: string[]) => {
            setFieldValue(`${type}[${idx}].data_categories`, newChecked);
          };
          const classifyDataFlow = classifyDataFlows?.find(
            (cdf) => cdf.fides_key === flow.fides_key
          );

          const mostLikelyCategories = classifyDataFlow?.classifications.map(
            ({ label, aggregated_score }) => ({
              ...dataCategoriesMap.get(label),
              fides_key: label,
              confidence: aggregated_score,
            })
          );
          let checked = flow.data_categories ?? [];
          if (checked.length === 0) {
            // If there are classifier suggestions, choose the highest-confidence option.
            if (mostLikelyCategories?.length) {
              const topCategory = mostLikelyCategories.reduce(
                (maxCat, nextCat) =>
                  (nextCat.confidence ?? 0) > (maxCat.confidence ?? 0)
                    ? nextCat
                    : maxCat
              );
              checked = [topCategory.fides_key];
            }
          }
          return (
            <AccordionItem
              key={flow.fides_key}
              pl={4}
              borderBottom="none"
              data-testid={`accordion-item-${flow.fides_key}`}
            >
              <AccordionItemContents headingLevel="h3" title={flow.fides_key}>
                {dataCategories ? (
                  <Box pr={2}>
                    <ClassifiedDataCategoryDropdown
                      mostLikelyCategories={mostLikelyCategories || []}
                      dataCategories={dataCategories}
                      checked={checked}
                      onChecked={handleChecked}
                    />
                  </Box>
                ) : null}
              </AccordionItemContents>
            </AccordionItem>
          );
        })}
      </AccordionItemContents>
    </AccordionItem>
  );
};

const DataFlowForm = ({
  onClose,
  system,
  onSave,
  classificationInstance,
}: {
  system: System;
  onSave: (flows: IngressEgress) => void;
  onClose: () => void;
  classificationInstance?: ClassifySystem;
}) => {
  const hasNoDataFlows =
    (system.ingress == null || system.ingress.length === 0) &&
    (system.egress == null || system.egress.length === 0);

  if (hasNoDataFlows) {
    return <Text>No data flows found on this system.</Text>;
  }

  const initialValues: IngressEgress = {
    egress: system.egress ?? [],
    ingress: system.ingress ?? [],
  };

  return (
    <Formik initialValues={initialValues} onSubmit={onSave}>
      <Form>
        <Stack>
          <Text fontWeight="semibold">{system.name}</Text>
          <Accordion allowMultiple pl={2}>
            <DataFlows
              classifyDataFlows={classificationInstance?.ingress}
              type="ingress"
            />
            <DataFlows
              classifyDataFlows={classificationInstance?.egress}
              type="egress"
            />
          </Accordion>
          <Box>
            <Button onClick={onClose} mr={2} size="sm" variant="outline">
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="primary"
              size="sm"
              data-testid="save-btn"
            >
              Save
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};

export default DataFlowForm;
