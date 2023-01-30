import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "@fidesui/react";
import { CustomTextArea } from "common/form/inputs";
import { Form, Formik } from "formik";
import React from "react";
import * as Yup from "yup";

type DenyModalProps = {
  isOpen: boolean;
  handleMenuClose: () => void;
  handleDenyRequest: (reason: string) => Promise<any>;
};

const handleSubmit = (
  handleMenuClose: () => void,
  handleDenyRequest: (reason: string) => Promise<any>,
  denialReason: string,
  setSubmitting: (isSubmitting: boolean) => void
) => {
  handleDenyRequest(denialReason).then(() => {
    setSubmitting(false);
    handleMenuClose();
  });
};

const DenyPrivacyRequestModal = ({
  isOpen,
  handleMenuClose,
  handleDenyRequest,
}: DenyModalProps) => (
  <Modal
    isOpen={isOpen}
    onClose={handleMenuClose}
    isCentered
    returnFocusOnClose={false}
  >
    <ModalOverlay />
    <ModalContent width="100%" maxWidth="456px">
      <Formik
        initialValues={{ denialReason: "" }}
        validationSchema={Yup.object({
          denialReason: Yup.string().required().label("Reason for denial"),
        })}
        onSubmit={(values, { setSubmitting }) => {
          handleSubmit(
            handleMenuClose,
            handleDenyRequest,
            values.denialReason,
            setSubmitting
          );
        }}
      >
        {({ isSubmitting, dirty, isValid }) => (
          <Form>
            <ModalHeader>Privacy Request Denial</ModalHeader>
            <ModalBody color="gray.500" fontSize="14px">
              Please enter a reason for denying this privacy request. Please
              note: this can be seen by the user in their notification email.
            </ModalBody>
            <ModalBody>
              <CustomTextArea
                name="denialReason"
                textAreaProps={{
                  focusBorderColor: "primary.600",
                  resize: "none",
                }}
              />
            </ModalBody>
            <ModalFooter>
              <Button
                size="sm"
                width="100%"
                maxWidth="198px"
                colorScheme="gray.200"
                mr={3}
                disabled={isSubmitting}
                onClick={handleMenuClose}
              >
                Close
              </Button>
              <Button
                type="submit"
                size="sm"
                width="100%"
                maxWidth="198px"
                colorScheme="primary"
                variant="solid"
                disabled={!dirty || !isValid}
                isLoading={isSubmitting}
              >
                Confirm
              </Button>
            </ModalFooter>
          </Form>
        )}
      </Formik>
    </ModalContent>
  </Modal>
);

export default DenyPrivacyRequestModal;
