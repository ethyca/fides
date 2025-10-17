import { ModalFuncProps } from "antd/es/modal";
import type { ModalStaticFunctions } from "antd/es/modal/confirm";
import { Form, FormInstance } from "antd/lib";
import React from "react";

/**
 * Options for the useFormModal hook. Extends modal options with the following changes:
 * - No onOk or onCancel props (handled by the hook for form validation and resetting)
 * - Content must be a function that receives the form instance and returns the content to display
 * @example content: (form) => <MyForm form={form} />
 */
export type UseFormModalOptions = Omit<
  ModalFuncProps,
  "onOk" | "onCancel" | "content"
> & {
  content: (form: FormInstance) => React.ReactNode;
};

/**
 * Generic hook for opening a modal with a form
 * @param modalApi - The modal API from useModal
 * @param options - The options for the modal
 * @returns Promise that resolves with form values or null if cancelled
 */
export const useFormModal = <T = any,>(
  modalApi: ModalStaticFunctions,
  options: UseFormModalOptions,
) => {
  const [form] = Form.useForm();

  const { content, ...modalOptions } = options;

  const openFormModal = React.useCallback(
    () =>
      new Promise<T | null>((resolve) => {
        modalApi.confirm({
          ...modalOptions,
          content: content(form),
          onOk: (closeModal) => {
            // on confirm, validate the form
            form
              .validateFields()
              .then((values) => {
                // if validation passes, close the modal, reset the form, and resolve with the values
                closeModal(values);
                form.resetFields();
                resolve(values);
              })
              .catch(() => {
                // if validation fails (eg. missing required fields), do nothing.
              });
          },
          onCancel: () => {
            // if modal is cancelled, reset the form and resolve with null.
            form.resetFields();
            resolve(null);
          },
        });
      }),
    [modalApi, form, content, modalOptions],
  );

  return { openFormModal, form };
};
