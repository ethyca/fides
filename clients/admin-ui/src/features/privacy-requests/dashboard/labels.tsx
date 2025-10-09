import { AntFlex as Flex, AntTag as Tag, AntText as Text } from "fidesui";

export const Label = ({ children }: React.PropsWithChildren) => {
  return <Text type="secondary">{children}</Text>;
};

type LabeledProps = React.PropsWithChildren<{ label: React.ReactNode }>;

export const LabeledTag = ({ label, children }: LabeledProps) => {
  return (
    <Flex gap={8} wrap>
      <Label>{label}:</Label>
      <Tag>{children}</Tag>
    </Flex>
  );
};

export const LabeledText = ({ label, children }: LabeledProps) => {
  return (
    <Flex gap={4} wrap>
      <Label>{label}:</Label>
      <Text>{children}</Text>
    </Flex>
  );
};
