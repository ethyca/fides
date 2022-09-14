import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  HStack,
  Input,
  Text,
} from "@fidesui/react";

import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
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
    data-testid={`declaration-${privacyDeclaration.name}`}
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
          <HStack data-testid="declaration-categories" mb="20px">
            <Text color="gray.600">Declaration categories</Text>
            {privacyDeclaration.data_categories.map((category) => (
              <TaxonomyEntityTag key={category} name={category} />
            ))}
          </HStack>
          <HStack data-testid="declaration-use" mb="20px">
            <Text color="gray.600">Data use</Text>
            <Input disabled value={privacyDeclaration.data_use} />
          </HStack>
          <HStack data-testid="declaration-subjects" mb="20px">
            <Text color="gray.600">Data subjects</Text>
            {privacyDeclaration.data_subjects.map((subject) => (
              <TaxonomyEntityTag name={subject} key={subject} />
            ))}
          </HStack>
          <HStack data-testid="declaration-qualifier" mb="20px">
            <Text color="gray.600">Data qualifier</Text>
            <Input disabled value={privacyDeclaration.data_qualifier} />
          </HStack>
        </AccordionPanel>
      </>
    </AccordionItem>
  </Accordion>
);

export default PrivacyDeclarationAccordion;
