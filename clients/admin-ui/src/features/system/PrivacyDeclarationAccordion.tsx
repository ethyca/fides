import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
} from "@fidesui/react";

import { PrivacyDeclaration } from "~/types/api";

import ConnectedPrivacyDeclarationForm from "./PrivacyDeclarationForm";

interface Props {
  privacyDeclaration: PrivacyDeclaration;
  onEdit?: (declaration: PrivacyDeclaration) => void;
}
const PrivacyDeclarationAccordion = ({ privacyDeclaration, onEdit }: Props) => {
  const handleEdit = (newValues: PrivacyDeclaration) => {
    if (onEdit) {
      onEdit(newValues);
    }
  };

  return (
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
            <ConnectedPrivacyDeclarationForm
              onSubmit={handleEdit}
              initialValues={privacyDeclaration}
            />
          </AccordionPanel>
        </>
      </AccordionItem>
    </Accordion>
  );
};

export default PrivacyDeclarationAccordion;
