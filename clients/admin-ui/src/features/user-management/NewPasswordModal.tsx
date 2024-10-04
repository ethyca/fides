import {
  AntButton,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import { useForceResetUserPasswordMutation } from "./user-management.slice";

const ValidationSchema = Yup.object().shape({
  password: passwordValidation.label("Password"),
  passwordConfirmation: Yup.string()
    .required()
    .oneOf([Yup.ref("password")], "Passwords must match")
    .label("Password confirmation"),
});
const initialValues = { password: "", passwordConfirmation: "" };
type FormValues = typeof initialValues;

const useNewPasswordModal = (id: string) => {
  const modal = useDisclosure();
  const toast = useToast();
  const [resetPassword] = useForceResetUserPasswordMutation();

  const handleResetPassword = async (values: FormValues) => {
    const result = await resetPassword({
      id,
      new_password: values.password,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          "Successfully reset user's password. Please inform the user of their new password.",
        ),
      );
      modal.onClose();
    }
  };

  return {
    ...modal,
    handleResetPassword,
  };
};

interface Props {
  id: string;
}

const NewPasswordModal = ({ id }: Props) => {
  const { handleResetPassword, isOpen, onClose, onOpen } =
    useNewPasswordModal(id);

  return (
    <>
      <AntButton onClick={onOpen} data-testid="reset-password-btn">
        Reset password
      </AntButton>
      <Modal isCentered isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <Formik
            initialValues={initialValues}
            validationSchema={ValidationSchema}
            onSubmit={handleResetPassword}
          >
            {({ isSubmitting, dirty, isValid }) => (
              <Form>
                <ModalHeader>Reset Password</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                  <Stack direction="column" spacing={4}>
                    <Text mb={2}>Choose a new password for this user.</Text>
                    <CustomTextInput
                      name="password"
                      label="Password"
                      placeholder="********"
                      type="password"
                      tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
                      autoComplete="new-password"
                    />
                    <CustomTextInput
                      name="passwordConfirmation"
                      label="Confirm Password"
                      placeholder="********"
                      type="password"
                      tooltip="Must match above password."
                      autoComplete="confirm-password"
                    />
                  </Stack>
                </ModalBody>

                <ModalFooter>
                  <div className="w-full gap-2">
                    <AntButton onClick={onClose} className="w-1/2">
                      Cancel
                    </AntButton>
                    <AntButton
                      type="primary"
                      disabled={!dirty || !isValid}
                      loading={isSubmitting}
                      htmlType="submit"
                      className="w-1/2"
                      data-testid="submit-btn"
                    >
                      Change Password
                    </AntButton>
                  </div>
                </ModalFooter>
              </Form>
            )}
          </Formik>
        </ModalContent>
      </Modal>
    </>
  );
};

export default NewPasswordModal;
