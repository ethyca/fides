import { Button, Spinner, VStack } from "@fidesui/react";
import { FieldArray, useFormikContext } from "formik";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCreatableSelect,
  CustomSelect,
} from "~/features/common/form/inputs";
import { selectDataUseOptions } from "~/features/data-use/data-use.slice";
import {
  selectDictDataUses,
  useGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import { transformDictDataUseToDeclaration } from "~/features/system/dictionary-form/helpers";

import {
  EMPTY_DECLARATION,
  FormValues,
  MinimalPrivacyDeclaration,
} from "./constants";

const DataUseBlock = ({
  index,
  isSuggestion,
}: {
  index: number;
  isSuggestion: boolean;
}) => {
  const dataUseOptions = useAppSelector(selectDataUseOptions);
  const textColor = isSuggestion ? "complimentary.500" : "gray.800";
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
        textColor={textColor}
      />
      <CustomCreatableSelect
        label="Cookie names"
        name={`privacy_declarations.${index}.cookies`}
        options={[]}
        variant="stacked"
        isMulti
        textColor={textColor}
      />
    </VStack>
  );
};

const DataUsesForm = ({ showSuggestions }: { showSuggestions: boolean }) => {
  const { values, setFieldValue } = useFormikContext<FormValues>();
  const { vendor_id: vendorId } = values;
  const { isLoading } = useGetDictionaryDataUsesQuery(
    { vendor_id: vendorId as string },
    { skip: !showSuggestions || vendorId == null }
  );
  const dictDataUses = useAppSelector(selectDictDataUses(vendorId || ""));

  useEffect(() => {
    if (showSuggestions && values.vendor_id && dictDataUses?.length) {
      const declarations: MinimalPrivacyDeclaration[] = dictDataUses
        .map((d) => transformDictDataUseToDeclaration(d))
        .map((d) => ({
          name: d.name ?? "",
          data_use: d.data_use,
          data_categories: d.data_categories,
          // TODO: fix this, we don't want to lose cookie info!
          cookies: d.cookies?.map((c) => c.name) || [],
        }));
      setFieldValue("privacy_declarations", declarations);
    }
  }, [showSuggestions, values.vendor_id, dictDataUses, setFieldValue]);

  if (isLoading) {
    return <Spinner size="sm" alignSelf="center" />;
  }

  return (
    <FieldArray
      name="privacy_declarations"
      render={(arrayHelpers) => (
        <>
          {values.privacy_declarations.map((declaration, idx) => (
            <DataUseBlock
              key={declaration.data_use || idx}
              index={idx}
              isSuggestion={showSuggestions}
            />
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
