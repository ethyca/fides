import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  HStack,
  Input,
  Tag,
  Text,
} from "@fidesui/react";

import { PrivacyDeclaration } from "~/types/api";

interface Props {
  privacyDeclaration: PrivacyDeclaration;
}
const PrivacyDeclarationAccordion = ({ privacyDeclaration }: Props) => (
  <Accordion
    allowToggle
    border="transparent"
    key={privacyDeclaration.name}
    m="5px !important"
    maxW="500px"
    minW="500px"
    width="500px"
  >
    <AccordionItem>
      <>
        <AccordionButton pr="0px" pl="0px">
          <Box flex="1" textAlign="left">
            {privacyDeclaration.name}
          </Box>
          <AccordionIcon />
        </AccordionButton>
        <AccordionPanel padding="0px" mt="20px">
          <HStack mb="20px">
            <Text color="gray.600">Declaration categories</Text>
            {privacyDeclaration.data_categories.map((category) => (
              <Tag
                background="primary.400"
                color="white"
                key={category}
                width="fit-content"
              >
                {category}
              </Tag>
            ))}
          </HStack>
          <HStack mb="20px">
            <Text color="gray.600">Data use</Text>
            <Input disabled value={privacyDeclaration.data_use} />
          </HStack>
          <HStack mb="20px">
            <Text color="gray.600">Data subjects</Text>
            {privacyDeclaration.data_subjects.map((subject) => (
              <Tag
                background="primary.400"
                color="white"
                key={subject}
                width="fit-content"
              >
                {subject}
              </Tag>
            ))}
          </HStack>
          <HStack mb="20px">
            <Text color="gray.600">Data qualifier</Text>
            <Input disabled value={privacyDeclaration.data_qualifier} />
          </HStack>
        </AccordionPanel>
      </>
    </AccordionItem>
  </Accordion>
);

export default PrivacyDeclarationAccordion;
