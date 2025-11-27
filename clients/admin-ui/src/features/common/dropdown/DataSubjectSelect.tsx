import {
  TaxonomySelect,
  TaxonomySelectOption,
  TaxonomySelectProps,
} from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";

const DataSubjectSelect = ({
  selectedTaxonomies,
  showDisabled = false,
  ...props
}: TaxonomySelectProps) => {
  const { getDataSubjectDisplayNameProps, getDataSubjects } = useTaxonomies();

  const getActiveDataSubjects = () =>
    getDataSubjects().filter((ds) => ds.active);

  const dataSubjects = showDisabled
    ? getDataSubjects()
    : getActiveDataSubjects();

  const options: TaxonomySelectOption[] = dataSubjects
    .filter((subject) => !selectedTaxonomies?.includes(subject.fides_key))
    .map((subject) => {
      const { name, primaryName } = getDataSubjectDisplayNameProps(
        subject.fides_key,
      );
      return {
        value: subject.fides_key,
        name,
        primaryName,
        description: subject.description || "",
        label: (
          <>
            <strong>{primaryName || name}</strong>
            {primaryName && `: ${name}`}
          </>
        ),
        title: subject.fides_key,
      };
    });
  return <TaxonomySelect options={options} {...props} />;
};

export default DataSubjectSelect;
