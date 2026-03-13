import { CustomTextArea } from "common/form/inputs";
import { Button, Flex, Modal } from "fidesui";
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
    [onDenyRequest, onClose],
  );
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        denialReason: Yup.string().required().label("Reason for denial"),
      })}
      onSubmit={handleSubmit}
    >
      {({ isSubmitting, dirty, isValid }) => (
        <Modal
          open={isOpen}
          onCancel={onClose}
          centered
          destroyOnHidden
          data-testid="deny-privacy-request-modal"
          title="Privacy request denial"
          footer={null}
        >
          <Form>
            <div className="mb-2 text-sm text-gray-500">
              Please enter a reason for denying this privacy request. Please
              note: this can be seen by the user in their notification email.
            </div>
            <CustomTextArea
              name="denialReason"
              textAreaProps={{
                focusBorderColor: "primary.600",
                resize: "none",
              }}
            />

            <Flex justify="flex-end" className="mt-4" gap="small">
              <Button disabled={isSubmitting} onClick={onClose}>
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={!dirty || !isValid}
                loading={isSubmitting}
                data-testid="deny-privacy-request-modal-btn"
              >
                Confirm
              </Button>
            </Flex>
          </Form>
        </Modal>
      )}
    </Formik>
  );
};

export default DenyPrivacyRequestModal;
