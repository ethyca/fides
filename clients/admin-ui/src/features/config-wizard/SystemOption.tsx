import { Box, Button, ButtonProps, Text } from "@fidesui/react";

const SystemOption = ({
  label,
  description,
  icon,
  onClick,
  ...buttonProps
}: {
  label: string;
  description: string;
  icon: React.ReactElement;
  onClick: () => void;
} & ButtonProps) => (
  <Button
    border="1px solid"
    borderColor="gray.300"
    borderRadius={8}
    p="4"
    variant="ghost"
    onClick={onClick}
    minHeight="116px"
    height="full"
    {...buttonProps}
  >
    <Box
      as="span"
      display="flex"
      flexDirection="column"
      alignItems="start"
      justifyContent="space-between"
      height="100%"
      width="100%"
      whiteSpace="break-spaces"
      textAlign="left"
    >
      <Box as="span" display="flex" alignItems="center">
        {icon}
        <Text fontWeight="semibold" color="gray.700" as="span" ml={3}>
          {label}
        </Text>
      </Box>
      <Text color="gray.500" as="span" fontWeight="medium">
        {description}
      </Text>
    </Box>
  </Button>
);

export default SystemOption;
