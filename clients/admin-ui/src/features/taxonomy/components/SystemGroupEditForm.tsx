import {
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput,
  AntSelect as Select,
  Icons,
  SparkleIcon,
} from "fidesui";
import { isEmpty, uniq, unset } from "lodash";
import { useMemo } from "react";

import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import AntColorSelect from "~/features/system/system-groups/components/AntColorSelect";
import { FormValues, TaxonomyEntity } from "~/features/taxonomy/types";
import { DataUse, SystemResponse } from "~/types/api";

interface SystemGroupEditFormProps {
  initialValues: TaxonomyEntity;
  onSubmit: (updatedTaxonomy: TaxonomyEntity) => void;
  formId: string;
  form: FormInstance;
  isDisabled?: boolean;
}

const ALL_SUGGESTED_VALUE = "all-suggested";

const SystemGroupEditForm = ({
  initialValues,
  onSubmit,
  form,
  formId,
  isDisabled,
}: SystemGroupEditFormProps) => {
  const handleFinish = (formValues: FormValues) => {
    const updatedTaxonomy: TaxonomyEntity = {
      ...initialValues,
      ...formValues,
    };
    if (
      !updatedTaxonomy?.rights?.values ||
      isEmpty(updatedTaxonomy?.rights?.values)
    ) {
      unset(updatedTaxonomy, "rights");
    }
    onSubmit(updatedTaxonomy);
  };

  const { data: dataUses = [], isLoading: isLoadingDataUses } =
    useGetAllDataUsesQuery();

  const { data: allSystems, isLoading: isLoadingSystems } =
    useGetAllSystemsQuery();

  const dataUseOptions = useMemo(
    () =>
      dataUses.map((dataUse: DataUse) => ({
        label: dataUse.name || dataUse.fides_key,
        value: dataUse.fides_key,
      })),
    [dataUses],
  );

  // Watch the current form values for systems to make suggestions dynamic
  const selectedSystemKeys = Form.useWatch("systems", form);

  const suggestedDataUses: string[] = useMemo(() => {
    const currentSelectedSystems = selectedSystemKeys || [];
    if (!allSystems || currentSelectedSystems.length === 0) {
      return [];
    }
    const selectedSystems: SystemResponse[] =
      allSystems?.filter((system) =>
        currentSelectedSystems.includes(system.fides_key),
      ) ?? [];
    return uniq(
      selectedSystems?.flatMap((system) =>
        system.privacy_declarations.map((d) => d.data_use),
      ),
    );
  }, [allSystems, selectedSystemKeys]);

  const systemOptions = useMemo(
    () =>
      allSystems?.map((system: SystemResponse) => ({
        label: system.name || system.fides_key,
        value: system.fides_key,
      })) ?? [],
    [allSystems],
  );

  const handleDataUseChange = (value: string[]) => {
    if (value.includes(ALL_SUGGESTED_VALUE)) {
      const newValue = uniq([
        ...suggestedDataUses,
        ...value.filter((v) => v !== ALL_SUGGESTED_VALUE),
      ]);
      form.setFieldsValue({ data_uses: newValue });
    } else {
      form.setFieldsValue({ data_uses: value });
    }
  };

  const dataUseOptionsGrouped = useMemo(() => {
    const suggestedOptions: { label: string; value: string }[] = [];
    const allOptions: { label: string; value: string }[] = [];
    dataUseOptions.forEach((opt) => {
      if (suggestedDataUses.includes(opt.value)) {
        suggestedOptions.push(opt);
      } else {
        allOptions.push(opt);
      }
    });

    if (suggestedOptions.length === 0) {
      return allOptions;
    }

    return [
      {
        label: "Select all suggested",
        value: ALL_SUGGESTED_VALUE,
      },
      {
        label: (
          <span className="flex items-center gap-2">
            <SparkleIcon />
            <strong>Suggested data uses</strong>
          </span>
        ),
        options: suggestedOptions,
      },
      {
        label: (
          <span className="flex items-center gap-2">
            <Icons.Document />
            <strong>All data uses</strong>
          </span>
        ),
        options: allOptions,
      },
    ];
  }, [dataUseOptions, suggestedDataUses]);

  return (
    <Form
      name={formId}
      initialValues={initialValues}
      onFinish={handleFinish}
      layout="vertical"
      form={form}
    >
      <Form.Item<string> label="Name" name="name">
        <AntInput data-testid="edit-taxonomy-form_name" disabled={isDisabled} />
      </Form.Item>
      <Form.Item<string> label="Description" name="description">
        <AntInput.TextArea
          rows={4}
          data-testid="edit-taxonomy-form_description"
          disabled={isDisabled}
        />
      </Form.Item>

      <Form.Item<string[]> label="Systems" name="systems">
        <Select
          mode="multiple"
          placeholder="Select systems"
          options={systemOptions}
          allowClear
          loading={isLoadingSystems}
          disabled={isDisabled}
          data-testid="edit-taxonomy-form_systems"
        />
      </Form.Item>

      <Form.Item<string> label="Color" name="label_color">
        <AntColorSelect
          disabled={isDisabled}
          data-testid="edit-taxonomy-form_color"
        />
      </Form.Item>

      <Form.Item<string[]> label="Data uses" name="data_uses">
        <Select
          mode="multiple"
          placeholder="Select data uses"
          options={dataUseOptionsGrouped}
          allowClear
          loading={isLoadingDataUses}
          disabled={isDisabled}
          onChange={handleDataUseChange}
          data-testid="edit-taxonomy-form_data_uses"
        />
      </Form.Item>
    </Form>
  );
};

export default SystemGroupEditForm;
