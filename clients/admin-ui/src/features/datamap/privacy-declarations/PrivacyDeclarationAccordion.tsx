import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Stack,
} from '@fidesui/react';
import { Form, Formik } from 'formik';

import { FormGuard } from '~/features/common/hooks/useIsAnyFormDirty';
import { PrivacyDeclarationWithId } from '~/features/datamap/privacy-declarations/types';

import {
  DataProps,
  PrivacyDeclarationFormComponents,
  usePrivacyDeclarationForm,
  ValidationSchema,
} from './PrivacyDeclarationForm';

interface AccordionProps extends DataProps {
  privacyDeclarations: PrivacyDeclarationWithId[];
  onEdit: (
    oldDeclaration: PrivacyDeclarationWithId,
    newDeclaration: PrivacyDeclarationWithId
  ) => Promise<boolean>;
  onDelete: (declaration: PrivacyDeclarationWithId) => Promise<boolean>;
}

const PrivacyDeclarationAccordionItem = ({
  privacyDeclaration,
  onEdit,
  onDelete,
  ...dataProps
}: { privacyDeclaration: PrivacyDeclarationWithId } & Omit<
  AccordionProps,
  'privacyDeclarations'
>) => {
  const handleEdit = (newValues: PrivacyDeclarationWithId) =>
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
              <FormGuard
                id={`${privacyDeclaration.data_use}-form`}
                name={privacyDeclaration.data_use}
              />
              <AccordionButton
                py={4}
                borderBottomWidth={isExpanded ? '0px' : '1px'}
                backgroundColor={isExpanded ? 'gray.50' : undefined}
                data-testid={`accordion-header-${privacyDeclaration.data_use}`}
              >
                {renderHeader({
                  dirty,
                  boxProps: { flex: '1', textAlign: 'left' },
                  hideSaved: !isExpanded,
                })}
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel backgroundColor="gray.50" pt={0}>
                <Stack spacing={4}>
                  <PrivacyDeclarationFormComponents
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
