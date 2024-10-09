import {
  CircleHelpIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Tooltip,
  VStack,
} from "fidesui";
import { useField } from "formik";

import {
  CustomSelect,
  Option,
  SelectInput,
} from "~/features/common/form/inputs";

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
      <VStack align="flex-start" w="full">
        <SelectInput
          fieldName="dataset"
          options={options}
          isMulti
          size="sm"
          isSearchable
        />
        {/* <FormErrorMessage>{error}</FormErrorMessage> */}
      </VStack>
    </FormControl>
    //   <div className="flex flex-row">
    //     <CustomSelect
    //       label="Datasets"
    //       labelProps={{
    //         fontWeight: "semibold",
    //         fontSize: "sm",
    //         minWidth: "150px",
    //       }}
    //       name="dataset"
    //       options={options}
    //       isMulti
    //       size="sm"
    //     />
    //     <Tooltip
    //       aria-label="Select a dataset to associate with this integration"
    //       hasArrow
    //       label="Select a dataset to associate with this integration"
    //       placement="right-start"
    //       openDelay={500}
    //     >
    //       <Flex alignItems="center" h="32px">
    //         <CircleHelpIcon marginLeft="8px" _hover={{ cursor: "pointer" }} />
    //       </Flex>
    //     </Tooltip>
    //   </div>
  );
};

export default SelectDataset;
