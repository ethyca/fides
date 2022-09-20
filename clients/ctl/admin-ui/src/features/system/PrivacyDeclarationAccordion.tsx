import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Stack,
  Text,
} from "@fidesui/react";

import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
import { PrivacyDeclaration } from "~/types/api";

import { DeclarationItem } from "./form-layout";

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
        <AccordionPanel px="0">
          <Stack spacing={2}>
            <DeclarationItem label="Data categories">
              {privacyDeclaration.data_categories.map((category) => (
                <TaxonomyEntityTag key={category} name={category} mr={1} />
              ))}
            </DeclarationItem>
            <DeclarationItem label="Data use">
              <TaxonomyEntityTag name={privacyDeclaration.data_use} />
            </DeclarationItem>
            <DeclarationItem label="Data subjects">
              {privacyDeclaration.data_subjects.map((subject) => (
                <TaxonomyEntityTag name={subject} key={subject} mr={1} />
              ))}
            </DeclarationItem>
            <DeclarationItem label="Data qualifier">
              {privacyDeclaration.data_qualifier ? (
                <TaxonomyEntityTag name={privacyDeclaration.data_qualifier} />
              ) : (
                "None"
              )}
            </DeclarationItem>
            <DeclarationItem label="Dataset references">
              {privacyDeclaration.dataset_references ? (
                <Text>{privacyDeclaration.dataset_references.join(", ")}</Text>
              ) : (
                "None"
              )}
            </DeclarationItem>
          </Stack>
        </AccordionPanel>
      </>
    </AccordionItem>
  </Accordion>
);

export default PrivacyDeclarationAccordion;
