import { ClassifiedDataCategoryDropdown } from "@fidesui/components";
import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Heading,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectDataCategories,
  selectDataCategoriesMap,
} from "~/features/taxonomy";
import { ClassifyDataFlow } from "~/types/api";

import { initialDataCategories } from "../plus/helpers";
import type { IngressEgress } from "./DataFlowForm";

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

const DataFlowsAccordionItem = ({
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
            // Use formik's method of indexing into array fields to update the value
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
          const checked = initialDataCategories({
            dataCategories: flow.data_categories,
            mostLikelyCategories,
          });
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

export default DataFlowsAccordionItem;
