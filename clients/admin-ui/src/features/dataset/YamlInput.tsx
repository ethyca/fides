import { Box, Text, Textarea } from "@fidesui/react";

const YamlInput = () => (
  <Box>
    <Text size="sm" color="gray.700" mb={4}>
      Get started creating your first dataset by pasting your dataset yaml
      below! You may have received this yaml from a colleague or your Ethyca
      developer support engineer.
    </Text>
    <Textarea
      fontFamily="Menlo"
      fontWeight={400}
      lineHeight="150%"
      color="gray.800"
      fontSize="13px"
    />
  </Box>
);

export default YamlInput;
