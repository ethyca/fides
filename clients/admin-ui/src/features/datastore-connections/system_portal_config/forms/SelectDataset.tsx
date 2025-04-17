import {
  AntSelect as Select,
  Box,
  FormControl,
  FormErrorMessage,
  FormLabel,
  VStack,
} from "fidesui";
import { useField } from "formik";

import { Option } from "~/features/common/form/inputs";
import { InfoTooltip } from "~/features/common/InfoTooltip";

const SelectDataset = ({ options }: { options?: Option[] }) => {
  const [field, { error }, helpers] = useField("dataset");
  const { setValue } = helpers;
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
          <Select
            {...field}
            id="dataset"
            placeholder="Select datasets..."
            options={options}
            onChange={(v) => setValue(v)}
            mode="multiple"
            className="w-full"
          />
        </Box>
        <FormErrorMessage>{error}</FormErrorMessage>
      </VStack>
      <div style={{ marginLeft: "8px" }}>
        <InfoTooltip label="Select datasets to associate with this integration" />
      </div>
    </FormControl>
  );
};

export default SelectDataset;
