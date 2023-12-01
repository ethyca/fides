import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  useDisclosure,
} from "@fidesui/react";
import { FieldArray, Form, Formik } from "formik";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCreatableSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { selectPurposes } from "~/features/common/purpose.slice";
import { useGetSystemPurposeSummaryQuery } from "~/features/plus/plus.slice";
import {
  MappedPurpose,
  SystemPurposeSummary,
  SystemResponse,
} from "~/types/api";

export const useConsentManagementModal = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return { isOpen, onOpen, onClose };
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  fidesKey: string;
};


type FormValues = SystemPurposeSummary;

export const ConsentManagementModal = ({
  isOpen,
  onClose,
  fidesKey,
}: Props) => {
  const { data: systemPurposeSummary, isLoading } =
    useGetSystemPurposeSummaryQuery(fidesKey);

  console.log(systemPurposeSummary, fidesKey);
  if (isLoading) {
    return <div> temp loading </div>;
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="xxl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent maxWidth="800px">
        <ModalHeader>Vendor</ModalHeader>
        <ModalBody>
          <Formik<FormValues>
            initialValues={systemPurposeSummary}
            enableReinitialize
            onSubmit={() => {}}
          >
            {({ values }) => (
              <Form>
                <CustomTextInput
                  label="Vendor Name"
                  variant="stacked"
                  name="name"
                  disabled
                />
                <FieldArray
                  name="purposes"
                  render={(arrayHelpers) => (
                    <Accordion>
                      {Object.entries(values.purposes).map(
                        ([purposeName, pdValues], index: number) => (
                          <AccordionItem>
                            <AccordionButton>
                              <Box flex="1" textAlign="left">
                                {purposeName}
                              </Box>
                              <AccordionIcon />
                            </AccordionButton>
                            <AccordionPanel>
                              <CustomCreatableSelect
                                label="Data Uses"
                                isMulti
                                disableMenu
                                isDisabled
                                variant="stacked"
                                name={`purposes['${purposeName}'].data_uses`}
                              />
                              <CustomCreatableSelect
                                label="Legal Basis"
                                isMulti
                                disableMenu
                                isDisabled
                                variant="stacked"
                                name={`purposes['${purposeName}'].legal_basis`}
                              />
                            </AccordionPanel>
                          </AccordionItem>
                        )
                      )}
                    </Accordion>
                  )}
                />
                <CustomCreatableSelect
                  label="Features"
                  isMulti
                  disableMenu
                  isDisabled
                  variant="stacked"
                  name="features"
                />
                <CustomCreatableSelect
                  label="Data Categories"
                  isMulti
                  disableMenu
                  isDisabled
                  variant="stacked"
                  name="data_categories"
                />
              </Form>
            )}
          </Formik>
        </ModalBody>

        <ModalFooter>
          <Button onClick={onClose}>Cancel</Button>
          <Button>Save</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
