import {
  AntButton as Button,
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
import { PasswordStrengthMeter } from "./PasswordStrengthMeter";
import { useState } from "react";

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
  const [newPasswordValue, setNewPasswordValue] = useState("");

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNewPasswordValue(event.target.value);
  };

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
    handleChange,
    newPasswordValue,
  };
};

interface Props {
  id: string;
}

const NewPasswordModal = ({ id }: Props) => {
  const {
    handleResetPassword,
    handleChange,
    newPasswordValue,
    isOpen,
    onClose,
    onOpen,
  } = useNewPasswordModal(id);

  return (
    <>
      <Button onClick={onOpen} data-testid="reset-password-btn">
        Reset password
      </Button>
      <Modal isCentered isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <Formik
            initialValues={initialValues}
            validationSchema={ValidationSchema}
            onSubmit={handleResetPassword}
          >
            {({ isSubmitting, dirty, isValid, values }) => (
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
                    <PasswordStrengthMeter password={values.password} pl={10} />
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
                    <Button onClick={onClose} className="w-1/2">
                      Cancel
                    </Button>
                    <Button
                      type="primary"
                      disabled={!dirty || !isValid}
                      loading={isSubmitting}
                      htmlType="submit"
                      className="w-1/2"
                      data-testid="submit-btn"
                    >
                      Change Password
                    </Button>
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
