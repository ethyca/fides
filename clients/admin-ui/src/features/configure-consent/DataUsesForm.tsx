import { Button, VStack } from "@fidesui/react";
import { FieldArray, useFormikContext } from "formik";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCreatableSelect,
  CustomSelect,
} from "~/features/common/form/inputs";
import { selectDataUseOptions } from "~/features/data-use/data-use.slice";

import { EMPTY_DECLARATION, FormValues } from "./constants";

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

const DataUsesForm = () => {
  const { values } = useFormikContext<FormValues>();
  return (
    <FieldArray
      name="privacy_declarations"
      render={(arrayHelpers) => (
        <>
          {values.privacy_declarations.map((declaration, idx) => (
            <DataUseBlock key={declaration.data_use || idx} index={idx} />
          ))}
          <Button
            size="xs"
            variant="ghost"
            colorScheme="complimentary"
            onClick={() => {
              arrayHelpers.push(EMPTY_DECLARATION);
            }}
            disabled={
              values.privacy_declarations[
                values.privacy_declarations.length - 1
              ]?.data_use === EMPTY_DECLARATION.data_use
            }
          >
            Add data use +
          </Button>
        </>
      )}
    />
  );
};

export default DataUsesForm;
