import DataTabs from "../common/DataTabs";
import DataCategoriesTab from "./DataCategoriesTab";
import DataSubjectsTab from "./DataSubjectsTab";
import DataUsesTab from "./DataUsesTab";
import IdentifiabilityTab from "./IdentifiabilityTab";

const TABS = [
  { label: "Data Categories", content: <DataCategoriesTab /> },
  { label: "Data Uses", content: <DataUsesTab /> },
  { label: "Data Subjects", content: <DataSubjectsTab /> },
  { label: "Identifiability", content: <IdentifiabilityTab /> },
];
const TaxonomyTabs = () => <DataTabs isLazy data={TABS} />;

export default TaxonomyTabs;
