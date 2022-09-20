import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Stack,
  Text,
} from "@fidesui/react";
import { useState } from "react";

import TaxonomyEntityTag from "~/features/taxonomy/TaxonomyEntityTag";
import { PrivacyDeclaration } from "~/types/api";

import { DeclarationItem } from "./form-layout";
import PrivacyDeclarationForm from "./PrivacyDeclarationForm";

const DeclarationReview = ({
  declaration,
}: {
  declaration: PrivacyDeclaration;
}) => (
  <Stack spacing={2}>
    <DeclarationItem label="Data categories">
      {declaration.data_categories.map((category) => (
        <TaxonomyEntityTag key={category} name={category} mr={1} />
      ))}
    </DeclarationItem>
    <DeclarationItem label="Data use">
      <TaxonomyEntityTag name={declaration.data_use} />
    </DeclarationItem>
    <DeclarationItem label="Data subjects">
      {declaration.data_subjects.map((subject) => (
        <TaxonomyEntityTag name={subject} key={subject} mr={1} />
      ))}
    </DeclarationItem>
    <DeclarationItem label="Data qualifier">
      {declaration.data_qualifier ? (
        <TaxonomyEntityTag name={declaration.data_qualifier} />
      ) : (
        "None"
      )}
    </DeclarationItem>
    <DeclarationItem label="Dataset references">
      {declaration.dataset_references ? (
        <Text>{declaration.dataset_references.join(", ")}</Text>
      ) : (
        "None"
      )}
    </DeclarationItem>
  </Stack>
);

interface Props {
  privacyDeclaration: PrivacyDeclaration;
  onEdit?: (declaration: PrivacyDeclaration) => void;
}
const PrivacyDeclarationAccordion = ({ privacyDeclaration, onEdit }: Props) => {
  const [isEditing, setIsEditing] = useState(false);
  const handleEdit = (newValues: PrivacyDeclaration) => {
    if (onEdit) {
      onEdit(newValues);
      setIsEditing(false);
    }
  };
  const showEditButton = onEdit && !isEditing;

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
            <Box mb={2}>
              {isEditing ? (
                <PrivacyDeclarationForm
                  onSubmit={handleEdit}
                  onCancel={() => setIsEditing(false)}
                  initialValues={privacyDeclaration}
                />
              ) : (
                <DeclarationReview declaration={privacyDeclaration} />
              )}
            </Box>
            {showEditButton ? (
              <Button
                size="sm"
                colorScheme="primary"
                data-testid="edit-btn"
                onClick={() => setIsEditing(!isEditing)}
              >
                Edit
              </Button>
            ) : null}
          </AccordionPanel>
        </>
      </AccordionItem>
    </Accordion>
  );
};

export default PrivacyDeclarationAccordion;
