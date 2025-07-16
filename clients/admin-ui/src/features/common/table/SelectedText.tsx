import { AntTypography as Typography } from "fidesui";

const { Text } = Typography;

export const SelectedText = ({ count }: { count: number }) => {
  return (
    <Text size="sm" strong data-testid="selected-count">
      {`${count} selected`}
    </Text>
  );
};
