import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Heading,
  Stack,
  Text,
} from "@fidesui/react";
import { ReactNode, useState } from "react";

import {
  ClassifyDataFlow,
  ClassifySystem,
  DataFlow,
  System,
} from "~/types/api";

import ClassifiedDataCategoryDropdown from "../dataset/ClassifiedDataCategoryDropdown";
import { useGetAllDataCategoriesQuery } from "../taxonomy";

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
  dataFlows,
  classifyDataFlows,
  type,
}: {
  dataFlows?: DataFlow[];
  classifyDataFlows?: ClassifyDataFlow[];
  type: "ingress" | "egress";
}) => {
  // Subscriptions
  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const dataCategoryMap = new Map(
    (dataCategories || []).map((dc) => [dc.fides_key, dc])
  );

  const [selectedDataCategories, setSelectedDataCategories] = useState<
    string[]
  >([]);

  if (dataFlows == null || dataFlows.length === 0) {
    return <Text p={4}>No {type}es found.</Text>;
  }

  return (
    <AccordionItem p={0}>
      <AccordionItemContents
        headingLevel="h2"
        title={`Connected ${
          type[0].toLocaleUpperCase() + type.slice(1)
        } Systems`}
      >
        {dataFlows.map((flow) => {
          const classifyDataFlow = classifyDataFlows?.find(
            (cdf) => cdf.fides_key === flow.fides_key
          );

          const mostLikelyCategories = classifyDataFlow?.classifications.map(
            ({ label, aggregated_score }) => ({
              ...dataCategoryMap.get(label),
              fides_key: label,
              confidence: aggregated_score,
            })
          );
          return (
            <AccordionItem key={flow.fides_key} pl={4} borderBottom="none">
              <AccordionItemContents headingLevel="h3" title={flow.fides_key}>
                {dataCategories ? (
                  <Box pr={2}>
                    <ClassifiedDataCategoryDropdown
                      mostLikelyCategories={mostLikelyCategories || []}
                      dataCategories={dataCategories}
                      checked={selectedDataCategories}
                      onChecked={setSelectedDataCategories}
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
  system,
  classificationInstance,
}: {
  system: System;
  classificationInstance?: ClassifySystem;
}) => {
  console.log({ system });

  const hasNoDataFlows =
    (system.ingress == null || system.ingress.length === 0) &&
    (system.egress == null || system.egress.length === 0);

  if (hasNoDataFlows) {
    return <Text>No data flows found on this system.</Text>;
  }

  return (
    <Stack>
      <Text fontWeight="semibold">{system.name}</Text>
      <Accordion allowMultiple pl={2}>
        <DataFlows
          dataFlows={system.ingress}
          classifyDataFlows={classificationInstance?.ingress}
          type="ingress"
        />
        <DataFlows
          dataFlows={system.egress}
          classifyDataFlows={classificationInstance?.egress}
          type="egress"
        />
      </Accordion>
    </Stack>
  );
};

export default DataFlowForm;
