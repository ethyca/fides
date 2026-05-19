import { Button, Card, Flex, Form, Icons, Select, Spin } from "fidesui";
import { useEffect } from "react";

import { useAppSelector } from "~/app/hooks";
import { dataUseIsConsentUse } from "~/features/configure-consent/dataUseIsConsentUse";
import {
  selectDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
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

interface DataUseBlockProps {
  index: number;
  disabled?: boolean;
}

const DataUseBlock = ({ index, disabled }: DataUseBlockProps) => {
  useGetAllDataUsesQuery();
  const allDataUseOptions = useAppSelector(selectDataUseOptions);

  const consentUse = Form.useWatch<string | undefined>([
    "privacy_declarations",
    index,
    "consent_use",
  ]);

  const detailedDataUseOptions = allDataUseOptions.filter(
    (o) => o.value.split(".")[0] === consentUse,
  );

  return (
    <Card size="small">
      <Flex vertical gap="middle">
        <Form.Item
          label="Consent category"
          tooltip="What is the system using the data for. For example, is it for third party advertising or perhaps simply providing system operations."
          name={[index, "consent_use"]}
          required
          rules={[{ required: true, message: "Consent category is required" }]}
          className="mb-0"
        >
          <Select
            options={CONSENT_USE_OPTIONS}
            disabled={disabled}
            aria-label="Consent category"
            data-testid={`select-consent-use-${index}`}
          />
        </Form.Item>
        <Form.Item
          label="Detailed consent category (optional)"
          tooltip="Select a more specific consent category"
          name={[index, "data_use"]}
          className="mb-0"
        >
          <Select
            allowClear
            options={detailedDataUseOptions}
            disabled={!consentUse || disabled}
            aria-label="Detailed consent category"
            data-testid={`select-data-use-${index}`}
          />
        </Form.Item>
        <Form.Item
          label="Cookie names"
          name={[index, "cookieNames"]}
          className="mb-0"
        >
          <Select
            mode="tags"
            options={[]}
            disabled={disabled}
            placeholder="Select..."
            className="w-full"
            aria-label="Cookie names"
            data-testid={`select-cookies-${index}`}
          />
        </Form.Item>
      </Flex>
    </Card>
  );
};

interface DataUsesFormProps {
  showSuggestions: boolean;
  isCreate: boolean;
  disabled?: boolean;
}

const DataUsesForm = ({
  showSuggestions,
  isCreate,
  disabled,
}: DataUsesFormProps) => {
  const form = Form.useFormInstance<FormValues>();
  const vendorId = Form.useWatch<string | undefined>("vendor_id", form);
  const privacyDeclarations = Form.useWatch<
    MinimalPrivacyDeclaration[] | undefined
  >("privacy_declarations", form);

  const { isLoading } = useGetDictionaryDataUsesQuery(
    { vendor_id: vendorId as string },
    { skip: !showSuggestions || vendorId === null || vendorId === undefined },
  );
  const dictDataUses = useAppSelector(selectDictDataUses(vendorId || ""));

  useEffect(() => {
    if (showSuggestions && vendorId && dictDataUses?.length) {
      const declarations: MinimalPrivacyDeclaration[] = dictDataUses
        .filter((du) => dataUseIsConsentUse(du.data_use))
        .map((d) => {
          const transformed = transformDictDataUseToDeclaration(d);
          const cookies = (d.cookies ?? []).map((c) => ({
            name: c.name,
            domain: c.domain,
            path: c.path ?? null,
          }));
          return {
            name: transformed.name ?? "",
            consent_use: transformed.data_use.split(".")[0],
            data_use: transformed.data_use,
            data_categories: transformed.data_categories,
            cookies,
            cookieNames: cookies.map((c) => c.name),
          };
        });
      form.setFieldValue("privacy_declarations", declarations);
    } else if (isCreate) {
      form.setFieldValue("privacy_declarations", [EMPTY_DECLARATION]);
    }
  }, [showSuggestions, isCreate, vendorId, dictDataUses, form]);

  const lastDeclaration = privacyDeclarations?.[privacyDeclarations.length - 1];
  const lastDataUseIsEmpty =
    lastDeclaration?.data_use === EMPTY_DECLARATION.data_use &&
    lastDeclaration?.consent_use === EMPTY_DECLARATION.consent_use;

  if (isLoading) {
    return <Spin size="small" />;
  }

  return (
    <Form.List name="privacy_declarations">
      {(fields, { add }) => (
        <Flex vertical gap="middle" align="stretch">
          {fields.map((field) => (
            <DataUseBlock
              key={field.key}
              index={field.name}
              disabled={disabled}
            />
          ))}
          <Flex justify="flex-start">
            <Button
              onClick={() => add(EMPTY_DECLARATION)}
              size="small"
              icon={<Icons.Add />}
              disabled={disabled || lastDataUseIsEmpty}
              data-testid="add-data-use-btn"
            >
              Add data use
            </Button>
          </Flex>
        </Flex>
      )}
    </Form.List>
  );
};

export default DataUsesForm;
