import { Box, BoxProps } from "fidesui";

const FormInfoBox = ({ children, ...props }: BoxProps) => {
  return (
    <Box
      p={4}
      mb={4}
      border="1px solid"
      borderColor="gray.200"
      bgColor="gray.50"
      borderRadius="md"
      {...props}
    >
      {children}
    </Box>
  );
};

export default FormInfoBox;
