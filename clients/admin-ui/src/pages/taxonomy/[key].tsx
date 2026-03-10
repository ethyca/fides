import type { NextPage } from "next";
import { useRouter } from "next/router";

import TaxonomyPageContent from "~/features/taxonomy/components/TaxonomyPageContent";

const TaxonomyPage: NextPage = () => {
  const {
    query: { key },
  } = useRouter();
  const initialTaxonomy = typeof key === "string" ? key : undefined;

  return <TaxonomyPageContent initialTaxonomy={initialTaxonomy} />;
};

export default TaxonomyPage;
