import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  ClassifiedDataCategoryDropdown,
  Heading,
  Text,
} from "fidesui";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import { sentenceCase } from "~/features/common/utils";
import { DataCategoryWithConfidence } from "~/features/dataset/types";
import { initialDataCategories } from "~/features/plus/helpers";
import {
  selectDataCategories,
  selectDataCategoriesMap,
} from "~/features/taxonomy";
import { ClassifyDataFlow, DataFlow } from "~/types/api";

import type { IngressEgress } from "./DataFlowsAccordion";

interface Props {
  classifyDataFlows?: ClassifyDataFlow[];
  type: "ingress" | "egress";
}

/**
 * AccordionItem styling wrapper
 */
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

/**
 * The individual accordion item for either an Ingress or Egress
 */
const DataFlowAccordionItem = ({
  flow,
  index,
  classifyDataFlows,
  type,
}: { flow: DataFlow; index: number } & Props) => {
  const { setFieldValue } = useFormikContext<IngressEgress>();
  const dataCategories = useAppSelector(selectDataCategories);
  const dataCategoriesMap = useAppSelector(selectDataCategoriesMap);

  const handleChecked = (newChecked: string[]) => {
    // Use formik's method of indexing into array fields to update the value
    setFieldValue(`${type}[${index}].data_categories`, newChecked);
  };
  const classifyDataFlow = classifyDataFlows?.find(
    (cdf) => cdf.fides_key === flow.fides_key,
  );

  const mostLikelyCategories: DataCategoryWithConfidence[] =
    classifyDataFlow?.classifications.map(({ label, score }) => ({
      ...dataCategoriesMap.get(label),
      fides_key: label,
      confidence: score,
    })) ?? [];
  const checked = initialDataCategories({
    dataCategories: flow.data_categories,
    mostLikelyCategories,
  });

  return (
    <AccordionItem
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
};

/**
 * The entire list of Ingresses or Egresses, rendered as an AccordionItem
 */
const DataFlowsAccordionItem = ({ classifyDataFlows, type }: Props) => {
  const { values } = useFormikContext<IngressEgress>();
  const flows = values[type];
  const typeLabel = {
    // When type is `ingress` display `sources`,
    ingress: "source",
    // and when type is `egress` display `destinations`
    egress: "destination",
  }[type];

  if (flows.length === 0) {
    return <Text p={4}>No {type}es found.</Text>;
  }

  return (
    <AccordionItem p={0} data-testid={`accordion-item-${type}`}>
      <AccordionItemContents
        headingLevel="h2"
        title={`Connected ${sentenceCase(typeLabel)} Systems`}
      >
        {flows.map((flow, idx) => (
          <DataFlowAccordionItem
            flow={flow}
            index={idx}
            classifyDataFlows={classifyDataFlows}
            type={type}
            key={flow.fides_key}
          />
        ))}
      </AccordionItemContents>
    </AccordionItem>
  );
};

export default DataFlowsAccordionItem;
