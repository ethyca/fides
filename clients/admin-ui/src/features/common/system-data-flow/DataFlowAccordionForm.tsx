import { DataFlow, System } from "~/types/api";
import {
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Button,
  Flex,
  Spacer,
  Stack,
  Tag,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useGetAllSystemsQuery } from "~/features/system";
import QuestionTooltip from "common/QuestionTooltip";
import { DataFlowSystemsDeleteTable } from "common/system-data-flow/DataFlowSystemsDeleteTable";
import DataFlowSystemsModal from "common/system-data-flow/DataFlowSystemsModal";
import React, { useEffect, useState } from "react";

import { GearLightIcon } from "common/Icon";
import { useUpdateUserManagedSystemsMutation } from "~/features/user-management";

type DataFlowAccordionItemProps = {
  isIngress?: boolean;
  dataFlows: DataFlow[];
};

export const DataFlowAccordionForm = ({
  dataFlows,
  isIngress,
}: DataFlowAccordionItemProps) => {
  const flowType = isIngress ? "Source" : "Destination";
  const pluralFlowType = `${flowType}s`;
  const dataFlowSystemsModal = useDisclosure();

  const { data: initialSystems } = useGetAllSystemsQuery(undefined, {
    // eslint-disable-next-line @typescript-eslint/no-shadow
    selectFromResult: ({ data }) => {
      const dataFlowKeys = dataFlows.map((f) => f.fides_key);
      return {
        data: data
          ? data.filter((s) => dataFlowKeys.indexOf(s.fides_key) > -1)
          : [],
      };
    },
  });

  const [assignedSystems, setAssignedSystems] =
    useState<System[]>(initialSystems);

  return (
    <AccordionItem>
      <AccordionButton height="44px" padding={2}>
        <Flex
          alignItems="center"
          justifyContent="start"
          flex={1}
          textAlign="left"
        >
          <Text fontSize="sm" lineHeight={5} fontWeight="semibold" mr={4}>
            {pluralFlowType}
          </Text>
          <QuestionTooltip label="helpful tip" />

          <Tag
            ml={2}
            backgroundColor="primary.400"
            borderRadius="6px"
            color="white"
          >
            {dataFlows.length}
          </Tag>
          <Spacer />
          <AccordionIcon />
        </Flex>
      </AccordionButton>
      <AccordionPanel backgroundColor="gray.50" padding={6}>
        <Stack
          borderRadius="md"
          backgroundColor="gray.50"
          aria-selected="true"
          spacing={4}
          data-testid="selected"
        >
          <>
            <Button
              colorScheme="primary"
              size="xs"
              width="fit-content"
              onClick={dataFlowSystemsModal.onOpen}
              data-testid="assign-systems-btn"
              rightIcon={<GearLightIcon />}
            >
              {`Configure ${pluralFlowType}`}
            </Button>
            <DataFlowSystemsDeleteTable
              dataFlowSystems={assignedSystems}
              onDataFlowSystemChange={setAssignedSystems}
            />
            {/* By conditionally rendering the modal, we force it to reset its state
                whenever it opens */}
            {dataFlowSystemsModal.isOpen ? (
              <DataFlowSystemsModal
                isOpen={dataFlowSystemsModal.isOpen}
                onClose={dataFlowSystemsModal.onClose}
                dataFlowSystems={assignedSystems}
                onDataFlowSystemChange={setAssignedSystems}
              />
            ) : null}
          </>
        </Stack>
      </AccordionPanel>
    </AccordionItem>
  );
};
