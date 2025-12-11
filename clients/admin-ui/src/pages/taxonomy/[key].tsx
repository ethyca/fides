import type { NextPage } from "next";
import { useRouter } from "next/router";

import TaxonomyPageContent from "~/features/taxonomy/components/TaxonomyPageContent";

const TaxonomyPage: NextPage = () => {
  const router = useRouter();
  const initialTaxonomy = router.query.key as string;

  return <TaxonomyPageContent initialTaxonomy={initialTaxonomy} />;
};

export default TaxonomyPage;
