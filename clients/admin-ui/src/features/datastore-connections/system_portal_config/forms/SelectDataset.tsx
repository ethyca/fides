import {
  Box,
  CircleHelpIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Tooltip,
  VStack,
} from "fidesui";
import { useField } from "formik";

import { Option, SelectInput } from "~/features/common/form/inputs";

const SelectDataset = ({ options }: { options?: Option[] }) => {
  const [, { error }] = useField("dataset");
  return (
    <FormControl display="flex">
      <FormLabel
        color="gray.900"
        fontWeight="semibold"
        fontSize="sm"
        htmlFor="dataset"
        minWidth="150px"
      >
        Datasets
      </FormLabel>
      <VStack align="flex-start" w="100%">
        <Box w="full">
          <SelectInput
            fieldName="dataset"
            options={options}
            isMulti
            size="sm"
            isSearchable
          />
        </Box>
        <FormErrorMessage>{error}</FormErrorMessage>
      </VStack>
      <Tooltip
        aria-label="Select datasets to associate with this integration"
        hasArrow
        label="Select datasets to associate with this integration"
        placement="right-start"
        openDelay={500}
      >
        <Flex alignItems="center" h="32px">
          <CircleHelpIcon marginLeft="8px" _hover={{ cursor: "pointer" }} />
        </Flex>
      </Tooltip>
    </FormControl>
  );
};

export default SelectDataset;
