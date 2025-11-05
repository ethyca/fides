import { AntFlex as Flex, AntText as Text } from "fidesui";

type LabeledProps = React.PropsWithChildren<{ label: React.ReactNode }>;

export const LabeledText = ({ label, children }: LabeledProps) => (
  <Flex gap="small" wrap>
    <Text type="secondary">{label}:</Text>
    <Text ellipsis={{ tooltip: true }} className="!max-w-60">
      {children}
    </Text>
  </Flex>
);
