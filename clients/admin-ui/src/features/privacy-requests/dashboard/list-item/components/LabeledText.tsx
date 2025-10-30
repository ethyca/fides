import { AntFlex as Flex, AntText as Text } from "fidesui";

type LabeledProps = React.PropsWithChildren<{ label: React.ReactNode }>;

export const LabeledText = ({ label, children }: LabeledProps) => (
  <Flex gap={4} wrap>
    <Text type="secondary">{label}:</Text>
    <Text>{children}</Text>
  </Flex>
);
