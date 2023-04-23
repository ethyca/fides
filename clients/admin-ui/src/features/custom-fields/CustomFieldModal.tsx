import {
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
import { ReactNode } from "react";
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
import * as Yup from "yup";
import {
  AllowedTypes,
  CustomFieldDefinition,
  ResourceTypes,
} from "~/types/api";
import {
  FIELD_TYPE_OPTIONS,
  RESOURCE_TYPE_OPTIONS,
} from "common/custom-fields";

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
}: ModalProps) => {
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
      >
        <CustomFieldHeader>Edit Custom Field</CustomFieldHeader>
        <ModalBody>
          <Formik
            initialValues={initialValuesTemplate}
            onSubmit={async () => {}}
          >
            <Form>
              <FormSection title="Field Information">
                <CustomTextInput label="Name" name="name" />
                <CustomTextInput label="Description" name="description" />
                <CustomSelect
                  label="Location"
                  name="resource_type"
                  options={RESOURCE_TYPE_OPTIONS}
                />
              </FormSection>
              <FormSection title="Configuration">
                <CustomSelect
                  label="Field Type"
                  name="field_type"
                  options={FIELD_TYPE_OPTIONS}
                />
              </FormSection>
            </Form>
          </Formik>
        </ModalBody>
        <ModalFooter>
          <SimpleGrid columns={2} width="100%">
            <Button
              variant="outline"
              mr={3}
              onClick={onClose}
              data-testid="cancel-btn"
              isDisabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              // onClick={onConfirm}
              data-testid="save-btn"
              isLoading={isLoading}
            >
              Save
            </Button>
          </SimpleGrid>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
