import { ColumnsType, Form, Switch, Table } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectPurposes } from "~/features/common/purpose.slice";

type FormPurposeOverride = {
  purpose: number;
  is_included: boolean;
  is_consent: boolean;
  is_legitimate_interest: boolean;
};

type FormPurposeOverrideWithIndex = FormPurposeOverride & {
  index: number;
};

const HIDDEN_PURPOSES = [1, 3, 4, 5, 6];

/**
 * @deprecated
 */
const DeprecatedPurposeOverrides = () => {
  const form = Form.useFormInstance<{
    purposeOverrides: FormPurposeOverride[];
  }>();
  const watchedOverrides = Form.useWatch("purposeOverrides", form);
  const purposeOverrides: FormPurposeOverride[] = useMemo(
    () => watchedOverrides ?? [],
    [watchedOverrides],
  );
  const { purposes: purposeMapping } = useAppSelector(selectPurposes);

  const dataSourceWithIndex: FormPurposeOverrideWithIndex[] = useMemo(
    () =>
      purposeOverrides.map((override, index) => ({
        ...override,
        index,
      })),
    [purposeOverrides],
  );

  const columns: ColumnsType<FormPurposeOverrideWithIndex> = useMemo(
    () => [
      {
        title: "TCF purpose",
        key: "purpose",
        render: (_, record) => (
          <>
            Purpose {record.purpose}: {purposeMapping[record.purpose]?.name}
          </>
        ),
      },
      {
        title: "Allowed",
        key: "allowed",
        width: 100,
        align: "center",
        render: (_, record) => (
          <Switch
            size="small"
            checked={record.is_included}
            onChange={(checked) => {
              const updated = [...purposeOverrides];
              updated[record.index] = {
                ...updated[record.index],
                is_included: checked,
                ...(checked
                  ? {}
                  : { is_consent: false, is_legitimate_interest: false }),
              };
              form.setFieldValue("purposeOverrides", updated);
            }}
            data-testid={`input-purposeOverrides[${record.index}].is_included`}
            className="mr-2"
          />
        ),
      },
      {
        title: "Consent",
        key: "consent",
        width: 100,
        align: "center",
        render: (_, record) => {
          if (HIDDEN_PURPOSES.includes(record.purpose)) {
            return null;
          }
          return (
            <Switch
              size="small"
              checked={record.is_consent}
              disabled={
                !purposeOverrides[record.index]?.is_included ||
                purposeOverrides[record.index]?.is_legitimate_interest
              }
              onChange={(checked) => {
                const updated = [...purposeOverrides];
                updated[record.index] = {
                  ...updated[record.index],
                  is_consent: checked,
                };
                form.setFieldValue("purposeOverrides", updated);
              }}
              data-testid={`input-purposeOverrides[${record.index}].is_consent`}
              className="mr-2"
            />
          );
        },
      },
      {
        title: "Legitimate interest",
        key: "legitimate_interest",
        width: 150,
        align: "center",
        render: (_, record) => {
          if (HIDDEN_PURPOSES.includes(record.purpose)) {
            return null;
          }
          return (
            <Switch
              size="small"
              checked={record.is_legitimate_interest}
              disabled={
                !purposeOverrides[record.index]?.is_included ||
                purposeOverrides[record.index]?.is_consent
              }
              onChange={(checked) => {
                const updated = [...purposeOverrides];
                updated[record.index] = {
                  ...updated[record.index],
                  is_legitimate_interest: checked,
                };
                form.setFieldValue("purposeOverrides", updated);
              }}
              data-testid={`input-purposeOverrides[${record.index}].is_legitimate_interest`}
              className="mr-2"
            />
          );
        },
      },
    ],
    [purposeMapping, purposeOverrides, form],
  );

  return (
    <Table
      dataSource={dataSourceWithIndex}
      columns={columns}
      rowKey="purpose"
      pagination={false}
      size="small"
      bordered
      data-testid="deprecated-purpose-overrides-table"
    />
  );
};
export default DeprecatedPurposeOverrides;
