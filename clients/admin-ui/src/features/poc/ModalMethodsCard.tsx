import {
  AntButton as Button,
  AntCard as Card,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntModal as modal,
  AntParagraph as Paragraph,
  useFormModal,
} from "fidesui";
import React from "react";

interface SampleFormProps {
  form: any;
}

const SampleForm = ({ form }: SampleFormProps) => {
  return (
    <Flex vertical gap={4}>
      <Paragraph>
        This is a sample form modal. Fill out the fields below and click
        confirm.
      </Paragraph>
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="Name"
          rules={[
            {
              required: true,
              message: "Please enter your name",
            },
          ]}
        >
          <Input placeholder="Enter your name" />
        </Form.Item>
      </Form>
    </Flex>
  );
};

export const ModalMethodsCard = () => {
  const [modalApi, modalApiContext] = modal.useModal();

  const renderFormContent = (form: any) => <SampleForm form={form} />;

  const { openFormModal } = useFormModal<{
    name: string;
    email: string;
    message: string;
  }>(modalApi as any, {
    title: "Custom form modal",
    content: renderFormContent,
    okText: "Submit",
    cancelText: "Cancel",
    width: 500,
    centered: true,
  });

  const showInfoModal = () => {
    modalApi.info({
      title: "Info modal",
      content: "This is an info modal with some information for the user.",
      okText: "Got it",
    });
  };

  const showSuccessModal = () => {
    modalApi.success({
      title: "Success modal",
      content: "Operation completed successfully!",
      okText: "Great",
    });
  };

  const showErrorModal = () => {
    modalApi.error({
      title: "Error modal",
      content: "Something went wrong. Please try again.",
      okText: "OK",
    });
  };

  const showWarningModal = () => {
    modalApi.warning({
      title: "Warning modal",
      content: "Please be careful with this action.",
      okText: "Understood",
    });
  };

  const showConfirmModal = () => {
    modalApi.confirm({
      title: "Confirm modal",
      content: "Are you sure you want to proceed with this action?",
      okText: "Yes",
      cancelText: "No",
    });
  };

  const showCustomFormModal = async () => {
    const result = await openFormModal();
    if (result) {
      modalApi.success({
        title: "Form submitted",
        content: `Form submitted successfully with name: ${result.name}`,
        okText: "OK",
      });
    }
  };

  return (
    <>
      {modalApiContext}
      <Card title="Modal methods" variant="borderless">
        <Flex gap={8}>
          <Button onClick={showCustomFormModal}>Show custom form modal</Button>
          <Button onClick={showInfoModal}>Show info modal</Button>
          <Button onClick={showSuccessModal}>Show success modal</Button>
          <Button onClick={showErrorModal}>Show error modal</Button>
          <Button onClick={showWarningModal}>Show warning modal</Button>
          <Button onClick={showConfirmModal} type="default">
            Show confirm modal
          </Button>
        </Flex>
      </Card>
    </>
  );
};
