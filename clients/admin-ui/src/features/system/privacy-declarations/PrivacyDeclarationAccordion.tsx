import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Stack,
} from "@fidesui/react";
import { Form, Formik } from "formik";

import { PrivacyDeclaration } from "~/types/api";

import {
  DataProps,
  PrivacyDeclarationFormComponents,
  usePrivacyDeclarationForm,
  ValidationSchema,
} from "./PrivacyDeclarationForm";

interface AccordionProps extends DataProps {
  privacyDeclarations: PrivacyDeclaration[];
  onEdit: (
    oldDeclaration: PrivacyDeclaration,
    newDeclaration: PrivacyDeclaration
  ) => Promise<boolean>;
}

const PrivacyDeclarationAccordionItem = ({
  privacyDeclaration,
  onEdit,
  ...dataProps
}: { privacyDeclaration: PrivacyDeclaration } & Omit<
  AccordionProps,
  "privacyDeclarations"
>) => {
  const handleEdit = (newValues: PrivacyDeclaration) =>
    onEdit(privacyDeclaration, newValues);

  const { initialValues, renderHeader, handleSubmit } =
    usePrivacyDeclarationForm({
      initialValues: privacyDeclaration,
      onSubmit: handleEdit,
      ...dataProps,
    });

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
            <Form data-testid={`${privacyDeclaration.data_use}-form`}>
              <AccordionButton
                py={4}
                borderBottomWidth={isExpanded ? "0px" : "1px"}
                backgroundColor={isExpanded ? "gray.50" : undefined}
                data-testid={`accordion-header-${privacyDeclaration.data_use}`}
              >
                {renderHeader({
                  dirty,
                  boxProps: { flex: "1", textAlign: "left" },
                  hideSaved: !isExpanded,
                })}
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
    {privacyDeclarations.map((dec, i) => (
      <PrivacyDeclarationAccordionItem
        // Privacy declarations don't have an enforced unique key right now
        // The closest is 'data_use' but that is only enforced on the frontend. Furthermore,
        // if it changes, it causes re-renders we don't need (so makes the "Saved" indicator disappear)
        // eslint-disable-next-line react/no-array-index-key
        key={i}
        privacyDeclaration={dec}
        {...props}
      />
    ))}
  </Accordion>
);

export default PrivacyDeclarationAccordion;
