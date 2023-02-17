import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Spinner,
  Stack,
} from "@fidesui/react";
import { Form, Formik } from "formik";

import { PrivacyDeclaration } from "~/types/api";

import {
  PrivacyDeclarationFormComponents,
  usePrivacyDeclarationForm,
  useTaxonomyData,
  ValidationSchema,
} from "./PrivacyDeclarationForm";

interface AccordionProps {
  privacyDeclarations: PrivacyDeclaration[];
  onEdit: (
    oldDeclaration: PrivacyDeclaration,
    newDeclaration: PrivacyDeclaration
  ) => Promise<boolean>;
}

const PrivacyDeclarationAccordionItem = ({
  privacyDeclaration,
  onEdit,
}: { privacyDeclaration: PrivacyDeclaration } & Pick<
  AccordionProps,
  "onEdit"
>) => {
  const handleEdit = (newValues: PrivacyDeclaration) =>
    onEdit(privacyDeclaration, newValues);

  const { isLoading, ...dataProps } = useTaxonomyData();
  const { initialValues, renderHeader, handleSubmit } =
    usePrivacyDeclarationForm({
      initialValues: privacyDeclaration,
      onSubmit: handleEdit,
      ...dataProps,
    });

  if (isLoading) {
    return <Spinner size="sm" />;
  }

  return (
    <AccordionItem>
      {({ isExpanded }) => (
        <Formik
          enableReinitialize
          initialValues={initialValues}
          onSubmit={handleSubmit}
          validationSchema={ValidationSchema}
        >
          {({ dirty }) => (
            <Form data-testid="privacy-declaration-form">
              <AccordionButton
                py={4}
                borderBottomWidth={isExpanded ? "0px" : "1px"}
                backgroundColor={isExpanded ? "gray.50" : undefined}
              >
                {renderHeader({ dirty, flex: "1", textAlign: "left" })}
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel backgroundColor="gray.50" pt={0}>
                <Stack spacing={4}>
                  <PrivacyDeclarationFormComponents {...dataProps} />
                </Stack>
              </AccordionPanel>
            </Form>
          )}
        </Formik>
      )}
    </AccordionItem>
  );
};

const PrivacyDeclarationAccordion = ({
  privacyDeclarations,
  ...props
}: AccordionProps) => (
  <Accordion
    allowToggle
    border="transparent"
    data-testid="privacy-declaration-accordion"
  >
    {privacyDeclarations.map((dec) => (
      <PrivacyDeclarationAccordionItem
        key={dec.data_use}
        privacyDeclaration={dec}
        {...props}
      />
    ))}
  </Accordion>
);

export default PrivacyDeclarationAccordion;
