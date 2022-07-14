import DataTabs from "../common/DataTabs";

const TABS = [
  { label: "Data Categories", content: <p>categories</p> },
  { label: "Data Uses", content: <p>uses</p> },
  { label: "Data Subjects", content: <p>subject</p> },
  { label: "Identifiability", content: <p>identifiability</p> },
];
const TaxonomyTabs = () => <DataTabs isLazy data={TABS} />;

export default TaxonomyTabs;
