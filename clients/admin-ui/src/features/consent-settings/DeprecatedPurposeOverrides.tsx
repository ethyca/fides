import { ColumnsType, Table } from "fidesui";
import { FieldArray, useFormikContext } from "formik";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { CustomSwitch } from "~/features/common/form/inputs";
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
  const { values, setFieldValue } = useFormikContext<{
    purposeOverrides: FormPurposeOverride[];
  }>();
  const { purposes: purposeMapping } = useAppSelector(selectPurposes);

  const dataSourceWithIndex: FormPurposeOverrideWithIndex[] = useMemo(
    () =>
      values.purposeOverrides.map((override, index) => ({
        ...override,
        index,
      })),
    [values.purposeOverrides],
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
          <CustomSwitch
            name={`purposeOverrides[${record.index}].is_included`}
            onChange={(checked) => {
              if (!checked) {
                setFieldValue(
                  `purposeOverrides[${record.index}].is_consent`,
                  false,
                );
                setFieldValue(
                  `purposeOverrides[${record.index}].is_legitimate_interest`,
                  false,
                );
              }
            }}
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
            <CustomSwitch
              isDisabled={
                !values.purposeOverrides[record.index].is_included ||
                values.purposeOverrides[record.index].is_legitimate_interest
              }
              name={`purposeOverrides[${record.index}].is_consent`}
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
            <CustomSwitch
              isDisabled={
                !values.purposeOverrides[record.index].is_included ||
                values.purposeOverrides[record.index].is_consent
              }
              name={`purposeOverrides[${record.index}].is_legitimate_interest`}
            />
          );
        },
      },
    ],
    [purposeMapping, values.purposeOverrides, setFieldValue],
  );

  return (
    <FieldArray
      name="purposeOverrides"
      render={() => (
        <Table
          dataSource={dataSourceWithIndex}
          columns={columns}
          rowKey="purpose"
          pagination={false}
          size="small"
          bordered
          data-testid="deprecated-purpose-overrides-table"
        />
      )}
    />
  );
};
export default DeprecatedPurposeOverrides;
