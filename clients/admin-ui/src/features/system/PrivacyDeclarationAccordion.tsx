import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Spinner,
  Text,
} from "@fidesui/react";

import { PrivacyDeclaration } from "~/types/api";

import { useGetDataUseByKeyQuery } from "../data-use/data-use.slice";
import ConnectedPrivacyDeclarationForm from "./PrivacyDeclarationForm";

interface Props {
  privacyDeclaration: PrivacyDeclaration;
  onEdit?: (declaration: PrivacyDeclaration) => void;
}
const PrivacyDeclarationAccordion = ({ privacyDeclaration, onEdit }: Props) => {
  const { data: dataUse, isLoading } = useGetDataUseByKeyQuery(
    privacyDeclaration.data_use
  );
  const handleEdit = (newValues: PrivacyDeclaration) => {
    if (onEdit) {
      onEdit(newValues);
    }
  };

  const title = dataUse?.name ?? privacyDeclaration.data_use;

  if (isLoading) {
    return <Spinner />;
  }

  return (
    <Accordion
      allowToggle
      border="transparent"
      key={privacyDeclaration.data_use}
      m="5px !important"
      data-testid={`declaration-${privacyDeclaration.data_use}`}
    >
      <AccordionItem>
        <>
          <AccordionButton pr="0px" pl="0px">
            <Text flex="1" textAlign="left" fontSize="sm" fontWeight="semibold">
              {title}
            </Text>
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
