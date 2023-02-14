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
import { Form, Formik, FormikHelpers } from "formik";
import React, { useCallback } from "react";
import * as Yup from "yup";

type DenyModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onDenyRequest: (reason: string) => Promise<any>;
};

const initialValues = { denialReason: "" };
type FormValues = typeof initialValues;
const DenyPrivacyRequestModal = ({
  isOpen,
  onClose,
  onDenyRequest,
}: DenyModalProps) => {
  const handleSubmit = useCallback(
    (values: FormValues, formikHelpers: FormikHelpers<FormValues>) => {
      const { setSubmitting } = formikHelpers;
      onDenyRequest(values.denialReason).then(() => {
        setSubmitting(false);
        onClose();
      });
    },
    [onDenyRequest, onClose]
  );
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      isCentered
      returnFocusOnClose={false}
    >
      <ModalOverlay />
      <ModalContent
        width="100%"
        maxWidth="456px"
        data-testid="deny-privacy-request-modal"
      >
        <Formik
          initialValues={initialValues}
          validationSchema={Yup.object({
            denialReason: Yup.string().required().label("Reason for denial"),
          })}
          onSubmit={handleSubmit}
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
                  onClick={onClose}
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
                  data-testid="deny-privacy-request-modal-btn"
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
};

export default DenyPrivacyRequestModal;
