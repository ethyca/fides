import { ModalFuncProps } from "antd/es/modal";
import type { ModalStaticFunctions } from "antd/es/modal/confirm";
import { Form, FormInstance } from "antd/lib";
import React from "react";

// options for the useFormModal hook are all options for the modal with the following changes:
// 1. no onOk or onCancel props as they will be handled by the hook to support form validation and resetting.
// 2. for content you must provide a function that receives the form instance and returns the content to display
// in the modal. Pass the form instance to your form component. eg. content: (form) => <MyForm form={form} />
export type UseFormModalOptions = Omit<
  ModalFuncProps,
  "onOk" | "onCancel" | "content"
> & {
  content: (form: FormInstance) => React.ReactNode;
};

// The useFormModal hooks is a generic hook that can be used to open a modal with a form.
// It's props are: modalApi (the modal api from useModal) and options (the options for the modal).
// It returns a promise that resolves with the values of the form or null if the modal is cancelled.
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
            form
              .validateFields()
              .then((values) => {
                closeModal(values);
                form.resetFields();
                resolve(values);
              })
              .catch(() => {});
          },
          onCancel: () => {
            form.resetFields();
            resolve(null);
          },
        });
      }),
    [modalApi, form, content, modalOptions],
  );

  return { openFormModal, form };
};
