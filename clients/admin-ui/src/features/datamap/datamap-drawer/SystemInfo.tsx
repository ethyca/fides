import { Divider, Flex, Form, Input, Title } from "fidesui";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { SystemInfoFormValues } from "~/features/datamap/datamap-drawer/types";
import { System } from "~/types/api";

type SystemInfoProps = {
  system: System;
};

export const SystemInfo = ({ system }: SystemInfoProps) => {
  const systemHref = `/systems/configure/${system.fides_key}`;
  return (
    <div>
      <Flex align="center">
        <Title level={5}>System details</Title>
        <div className="grow" />
        <RouterLink href={systemHref}>View more</RouterLink>
      </Flex>
      <Divider size="small" className="pb-4" />
      <Form
        layout="vertical"
        initialValues={system as SystemInfoFormValues}
        key={system.fides_key}
      >
        <Form.Item name="name" label="System name">
          <Input disabled data-testid="input-name" />
        </Form.Item>
        <Form.Item name="description" label="System description">
          <Input.TextArea disabled data-testid="input-description" />
        </Form.Item>
      </Form>
    </div>
  );
};
