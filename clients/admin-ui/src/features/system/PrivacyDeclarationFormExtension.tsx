import { CustomSelect } from "../common/form/inputs";
import { useGetAllDatasetsQuery } from "../dataset";

const PrivacyDeclarationFormExtension = () => {
  const { data: datasets } = useGetAllDatasetsQuery();
  const datasetOptions = datasets
    ? datasets.map((d) => ({
        label: d.name ?? d.fides_key,
        value: d.fides_key,
      }))
    : [];

  return (
    <CustomSelect
      name="dataset_references"
      label="Dataset references"
      options={datasetOptions}
      tooltip="Referenced Dataset fides keys used by the system."
      isMulti
    />
  );
};

export default PrivacyDeclarationFormExtension;
