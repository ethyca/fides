import { Button, Spinner, VStack } from "@fidesui/react";
import { FieldArray, useFormikContext } from "formik";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCreatableSelect,
  CustomSelect,
} from "~/features/common/form/inputs";
import { dataUseIsConsentUse } from "~/features/configure-consent/vendor-transform";
import { selectDataUseOptions } from "~/features/data-use/data-use.slice";
import {
  selectDictDataUses,
  useGetDictionaryDataUsesQuery,
} from "~/features/plus/plus.slice";
import { transformDictDataUseToDeclaration } from "~/features/system/dictionary-form/helpers";

import {
  CONSENT_USE_OPTIONS,
  EMPTY_DECLARATION,
  FormValues,
  MinimalPrivacyDeclaration,
} from "./constants";

const DataUseBlock = ({
  index,
  isSuggestion,
  disableFields,
}: {
  index: number;
  isSuggestion: boolean;
  disableFields: boolean;
}) => {
  const allDataUseOptions = useAppSelector(selectDataUseOptions);
  const textColor = isSuggestion ? "complimentary.500" : "gray.800";

  const { values } = useFormikContext<FormValues>();

  const detailedDataUseOptions = allDataUseOptions.filter(
    (o) =>
      o.value.split(".")[0] === values.privacy_declarations[index].consent_use
  );

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
        name={`privacy_declarations.${index}.consent_use`}
        options={CONSENT_USE_OPTIONS}
        variant="stacked"
        isRequired
        isCustomOption
        singleValueBlock
        textColor={textColor}
        isDisabled={disableFields}
      />
      <CustomSelect
        label="Detailed data use (optional)"
        tooltip="Select a more specific data use"
        name={`privacy_declarations.${index}.data_use`}
        options={detailedDataUseOptions}
        variant="stacked"
        isCustomOption
        singleValueBlock
        textColor={textColor}
        isDisabled={
          !values.privacy_declarations[index].consent_use || disableFields
        }
      />
      <CustomCreatableSelect
        label="Cookie names"
        name={`privacy_declarations.${index}.cookieNames`}
        options={[]}
        variant="stacked"
        isMulti
        textColor={textColor}
        isDisabled={disableFields}
      />
    </VStack>
  );
};

const DataUsesForm = ({
  showSuggestions,
  disableFields,
}: {
  showSuggestions: boolean;
  disableFields: boolean;
}) => {
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
        .filter((du) => dataUseIsConsentUse(du.data_use))
        .map((d) => transformDictDataUseToDeclaration(d))
        .map((d) => ({
          name: d.name ?? "",
          consent_use: d.data_use.split(".")[0],
          data_use: d.data_use,
          data_categories: d.data_categories,
          cookieNames: d.cookies?.map((c) => c.name) || [],
          cookies: d.cookies ?? [],
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
              disableFields={disableFields}
            />
          ))}
          {!disableFields ? (
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
                ]?.data_use === EMPTY_DECLARATION.data_use &&
                values.privacy_declarations[
                  values.privacy_declarations.length - 1
                ]?.consent_use === EMPTY_DECLARATION.consent_use
              }
              data-testid="add-data-use-btn"
            >
              Add data use +
            </Button>
          ) : null}
        </>
      )}
    />
  );
};

export default DataUsesForm;
