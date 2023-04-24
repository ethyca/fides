import {
  Box,
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
} from "@fidesui/react";
import {
  FIELD_TYPE_OPTIONS,
  RESOURCE_TYPE_OPTIONS,
} from "common/custom-fields";
import FormSection from "common/form/FormSection";
import { CustomSelect, CustomTextInput } from "common/form/inputs";
import {
  Field,
  FieldInputProps,
  Form,
  Formik,
  FormikHelpers,
  FormikProps,
} from "formik";
import { ReactNode, useRef } from "react";
import * as Yup from "yup";

import { CreateCustomLists } from "~/features/common/custom-fields/CreateCustomLists";
import {
  AllowedTypes,
  CustomFieldDefinition,
  CustomFieldDefinitionWithId,
  ResourceTypes,
} from "~/types/api";

type HeaderProps = {
  children: ReactNode;
};

const CustomFieldHeader = ({ children }: HeaderProps) => (
  <ModalHeader
    id="modal-header"
    fontWeight="semibold"
    lineHeight={5}
    fontSize="sm"
    textAlign="left"
    py="18px"
    px={6}
    height="56px"
    backgroundColor="gray.50"
    borderColor="gray.200"
    borderWidth="0px 0px 1px 1p"
    borderTopRightRadius="8px"
    borderTopLeftRadius="8px"
    boxSizing="border-box"
  >
    {children}
  </ModalHeader>
);

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
  customField?: CustomFieldDefinitionWithId;
};

const initialValuesTemplate: CustomFieldDefinition = {
  description: undefined,
  field_type: AllowedTypes.STRING,
  name: "",
  resource_type: ResourceTypes.DATA_CATEGORY,
};

export const CustomFieldModal = ({
  isOpen,
  onClose,
  isLoading,
  customField,
}: ModalProps) => {
  const initialValues = customField ?? initialValuesTemplate;
  const createCustomListsRef = useRef(null);

  return (
    <Modal
      id="custom-field-modal-hello-world"
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent
        id="modal-content"
        textAlign="center"
        data-testid="custom-field-modal"
        maxHeight="80%"
        overflowY="auto"
      >
        <CustomFieldHeader>Edit Custom Field</CustomFieldHeader>
        <ModalBody px={6} py={0}>
          <Formik initialValues={initialValues} onSubmit={async () => {}}>
            {({ dirty, isValid, isSubmitting }) => (
              <Form
                style={{
                  paddingTop: "12px",
                  paddingBottom: "12px",
                }}
              >
                <Box py={3}>
                  <FormSection title="Field Information">
                    <CustomTextInput label="Name" name="name" />
                    <CustomTextInput label="Description" name="description" />
                    <CustomSelect
                      label="Location"
                      name="resource_type"
                      options={RESOURCE_TYPE_OPTIONS}
                    />
                  </FormSection>
                </Box>
                <Box py={3}>
                  <FormSection title="Configuration">
                    <CustomSelect
                      label="Field Type"
                      name="field_type"
                      options={FIELD_TYPE_OPTIONS}
                    />
                    <CreateCustomLists
                      onSubmitComplete={() => {}}
                      ref={createCustomListsRef}
                    />
                  </FormSection>
                </Box>

                <SimpleGrid columns={2} width="100%">
                  <Button
                    variant="outline"
                    mr={3}
                    onClick={onClose}
                    data-testid="cancel-btn"
                    isDisabled={isLoading || isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    colorScheme="primary"
                    data-testid="save-btn"
                    isLoading={isLoading}
                    isDisabled={!dirty || !isValid || isSubmitting}
                  >
                    Save
                  </Button>
                </SimpleGrid>
              </Form>
            )}
          </Formik>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
