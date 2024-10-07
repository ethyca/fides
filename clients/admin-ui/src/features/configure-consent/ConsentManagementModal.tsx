/* eslint-disable react/no-array-index-key */
import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  AntButton as Button,
  Box,
  Flex,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spacer,
  Spinner,
  useDisclosure,
} from "fidesui";
import { FieldArray, Form, Formik } from "formik";

import {
  CustomCreatableSelect,
  CustomTextInput,
  Label,
} from "~/features/common/form/inputs";
import { useGetSystemPurposeSummaryQuery } from "~/features/plus/plus.slice";
import { SystemPurposeSummary } from "~/types/api";

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
          {isLoading ? (
            <Flex
              width="100%"
              height="324px"
              alignItems="center"
              justifyContent="center"
            >
              <Spinner />
            </Flex>
          ) : (
            <Formik<FormValues>
              initialValues={
                systemPurposeSummary as unknown as SystemPurposeSummary
              }
              enableReinitialize
              onSubmit={() => {}}
            >
              {({ values }) => (
                <Form>
                  <Box mb={6}>
                    <CustomTextInput
                      label="Vendor Name"
                      variant="stacked"
                      name="name"
                      disabled
                    />
                  </Box>
                  {Object.entries(values?.purposes || {}).length > 0 ? (
                    <Label> Purposes </Label>
                  ) : null}
                  <FieldArray
                    name="purposes"
                    render={() => (
                      <Accordion allowMultiple>
                        {Object.entries(values.purposes).map(
                          ([purposeName], index: number) => (
                            <AccordionItem key={index}>
                              {({ isExpanded }) => (
                                <>
                                  <AccordionButton
                                    backgroundColor={
                                      isExpanded ? "gray.50" : "unset"
                                    }
                                  >
                                    <Box flex="1" textAlign="left">
                                      {purposeName}
                                    </Box>
                                    <AccordionIcon />
                                  </AccordionButton>
                                  <AccordionPanel backgroundColor="gray.50">
                                    <Box my={4}>
                                      <CustomCreatableSelect
                                        label="Data Uses"
                                        isMulti
                                        disableMenu
                                        isDisabled
                                        options={[]}
                                        variant="stacked"
                                        name={`purposes['${purposeName}'].data_uses`}
                                      />
                                    </Box>
                                    <CustomCreatableSelect
                                      label="Legal Basis"
                                      isMulti
                                      disableMenu
                                      isDisabled
                                      options={[]}
                                      variant="stacked"
                                      name={`purposes['${purposeName}'].legal_bases`}
                                    />
                                  </AccordionPanel>
                                </>
                              )}
                            </AccordionItem>
                          ),
                        )}
                      </Accordion>
                    )}
                  />
                  <Box my={4}>
                    <CustomCreatableSelect
                      label="Features"
                      isMulti
                      options={[]}
                      disableMenu
                      isDisabled
                      variant="stacked"
                      name="features"
                    />
                  </Box>
                  <CustomCreatableSelect
                    label="Data Categories"
                    isMulti
                    options={[]}
                    disableMenu
                    isDisabled
                    variant="stacked"
                    name="data_categories"
                  />
                </Form>
              )}
            </Formik>
          )}
        </ModalBody>

        <ModalFooter>
          <Button size="small" onClick={onClose}>
            Close{" "}
          </Button>
          <Spacer />
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
