import { VStack } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCreatableSelect,
  CustomSelect,
} from "~/features/common/form/inputs";

import { selectDataUseOptions } from "../data-use/data-use.slice";

const DataUseBlock = ({ index }: { index: number }) => {
  const dataUseOptions = useAppSelector(selectDataUseOptions);
  return (
    <VStack
      width="100%"
      borderRadius="4px"
      border="1px solid"
      borderColor="gray.200"
      spacing={4}
      p={4}
    >
      <CustomSelect
        label="Data use"
        tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
        name={`privacy_declarations.${index}.data_use`}
        options={dataUseOptions}
        variant="stacked"
      />
      <CustomCreatableSelect
        label="Cookie names"
        name={`privacy_declarations.${index}.cookies`}
        options={[]}
        variant="stacked"
        isMulti
      />
    </VStack>
  );
};

export default DataUseBlock;
