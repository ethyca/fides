import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Stack,
} from "@fidesui/react";
import { Form, Formik } from "formik";

import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";

import {
  DataProps,
  PrivacyDeclarationFormComponents,
  usePrivacyDeclarationForm,
  ValidationSchema,
} from "./PrivacyDeclarationForm";
import { PrivacyDeclarationWithId } from "./types";

interface AccordionProps extends DataProps {
  privacyDeclarations: PrivacyDeclarationWithId[];
  onEdit: (
    oldDeclaration: PrivacyDeclarationWithId,
    newDeclaration: PrivacyDeclarationWithId
  ) => Promise<PrivacyDeclarationWithId[] | undefined>;
  onDelete: (
    declaration: PrivacyDeclarationWithId
  ) => Promise<PrivacyDeclarationWithId[] | undefined>;
}

const PrivacyDeclarationAccordionItem = ({
  privacyDeclaration,
  onEdit,
  onDelete,
  ...dataProps
}: { privacyDeclaration: PrivacyDeclarationWithId } & Omit<
  AccordionProps,
  "privacyDeclarations"
>) => {
  const handleEdit = (values: PrivacyDeclarationWithId) =>
    onEdit(privacyDeclaration, values);

  const { initialValues, renderHeader, handleSubmit } =
    usePrivacyDeclarationForm({
      initialValues: privacyDeclaration,
      onSubmit: handleEdit,
      privacyDeclarationId: privacyDeclaration.id,
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
              <FormGuard
                id={`${privacyDeclaration.id}-form`}
                name={privacyDeclaration.id}
              />
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
                  <PrivacyDeclarationFormComponents
                    privacyDeclarationId={privacyDeclaration.id}
                    onDelete={onDelete}
                    {...dataProps}
                  />
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
        // This isn't a perfect key as privacy declarations don't have an enforced key right now.
        // The closest is 'data_use' but that is only enforced on the frontend and can change
        // This results in the "Saved" indicator not appearing if you change the 'data_use' in the form
        // The fix would be to enforce a key, either on the backend, or through a significant workaround on the frontend
        key={dec.id}
        privacyDeclaration={dec}
        {...props}
      />
    ))}
  </Accordion>
);

export default PrivacyDeclarationAccordion;
