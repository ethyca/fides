import { Form, FormInstance, Input, Select } from "fidesui";
import { uniq } from "lodash";
import { useEffect, useMemo, useState } from "react";

import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import { useGetAllSystemsQuery } from "~/features/system";
import { ColorSelect } from "~/features/system/system-groups/components/ColorSelect";
import { DataUseSelectWithSuggestions } from "~/features/system/system-groups/components/DataUseSelectWithSuggestions";
import {
  CustomTaxonomyColor,
  DataUse,
  SystemGroupCreate,
  SystemResponse,
} from "~/types/api";

interface CreateSystemGroupFormProps {
  form: FormInstance<SystemGroupCreate>;
  selectedSystemKeys?: string[];
  onSubmit: (values: SystemGroupCreate) => void;
}

export const useCreateSystemGroupForm = () => {
  const [form] = Form.useForm<SystemGroupCreate>();
  const values = Form.useWatch([], form);
  const [isSubmittable, setIsSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setIsSubmittable(true))
      .catch(() => setIsSubmittable(false));
  }, [form, values]);

  return { form, isSubmittable };
};

export const CreateSystemGroupForm = ({
  form,
  selectedSystemKeys = [],
  onSubmit,
}: CreateSystemGroupFormProps) => {
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

  const suggestedDataUses: string[] = useMemo(() => {
    const selectedSystems: SystemResponse[] =
      allSystems?.filter((system) =>
        selectedSystemKeys.includes(system.fides_key),
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

  const initialValues: SystemGroupCreate = {
    name: "",
    description: "",
    label_color: CustomTaxonomyColor.TAXONOMY_WHITE,
    systems: selectedSystemKeys,
    data_uses: [],
    active: true,
  };

  return (
    <Form
      form={form}
      initialValues={initialValues}
      onFinish={onSubmit}
      layout="vertical"
    >
      <Form.Item
        name="name"
        label="Name"
        required
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input placeholder="Enter system group name" data-testid="input-name" />
      </Form.Item>

      <Form.Item name="description" label="Description">
        <Input.TextArea
          placeholder="Enter system group description"
          data-testid="input-description"
        />
      </Form.Item>

      <Form.Item name="systems" label="Systems">
        <Select
          mode="multiple"
          aria-label="Systems"
          placeholder="Select systems"
          options={systemOptions}
          allowClear
          loading={isLoadingSystems}
        />
      </Form.Item>

      <Form.Item
        name="label_color"
        label="Color"
        required
        rules={[{ required: true, message: "Color is required" }]}
      >
        <ColorSelect />
      </Form.Item>

      <Form.Item name="data_uses" label="Data uses">
        <DataUseSelectWithSuggestions
          options={dataUseOptions}
          loading={isLoadingDataUses}
          suggestedDataUses={suggestedDataUses}
        />
      </Form.Item>
    </Form>
  );
};
