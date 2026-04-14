import {
  Divider,
  Flex,
  Form,
  Input,
  Title,
  Typography,
  useMessage,
} from "fidesui";
import NextLink from "next/link";

import { getErrorMessage } from "~/features/common/helpers";
import { SystemInfoFormValues } from "~/features/datamap/datamap-drawer/types";
import { useUpsertSystemsMutation } from "~/features/system/system.slice";
import { System } from "~/types/api";
import { isErrorResult } from "~/types/errors/api";

type SystemInfoProps = {
  system: System;
};

const useSystemInfo = (
  system: System,
  form: ReturnType<typeof Form.useForm<SystemInfoFormValues>>[0],
) => {
  const [upsertSystem] = useUpsertSystemsMutation();
  const message = useMessage();
  const handleUpsertSystem = async (values: SystemInfoFormValues) => {
    const requestBody: System[] = [
      {
        ...system,
        name: values.name,
        description: values.description,
      },
    ];

    const result = await upsertSystem(requestBody);
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Successfully saved system info");
      form.setFieldsValue(values);
    }
  };

  return { handleUpsertSystem };
};

export const SystemInfo = ({ system }: SystemInfoProps) => {
  const systemHref = `/systems/configure/${system.fides_key}`;
  const [form] = Form.useForm<SystemInfoFormValues>();

  const { handleUpsertSystem } = useSystemInfo(system, form);
  return (
    <div>
      <Flex align="center">
        <Title level={5}>System details</Title>
        <div className="grow" />
        <NextLink href={systemHref} passHref legacyBehavior>
          <Typography.Link>View more</Typography.Link>
        </NextLink>
      </Flex>
      <Divider size="small" className="pb-4" />
      <Form
        form={form}
        layout="vertical"
        initialValues={system as SystemInfoFormValues}
        onFinish={handleUpsertSystem}
        key={system.fides_key}
      >
        <Form.Item
          name="name"
          label="System name"
          rules={[{ required: true, message: "Name is required" }]}
        >
          <Input disabled data-testid="input-name" />
        </Form.Item>
        <Form.Item
          name="description"
          label="System description"
          rules={[{ required: true, message: "Description is required" }]}
        >
          <Input.TextArea disabled data-testid="input-description" />
        </Form.Item>
      </Form>
    </div>
  );
};
