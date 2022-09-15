import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Grid,
  GridItem,
  Stack,
  Text,
} from "@fidesui/react";
import { ReactNode } from "react";

import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
import { PrivacyDeclaration } from "~/types/api";

const DeclarationItem = ({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) => (
  <Grid templateColumns="1fr 2fr" data-testid={`declaration-${label}`}>
    <GridItem>
      <Text color="gray.600">{label}</Text>
    </GridItem>
    <GridItem>{children}</GridItem>
  </Grid>
);
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
          </Stack>
        </AccordionPanel>
      </>
    </AccordionItem>
  </Accordion>
);

export default PrivacyDeclarationAccordion;
