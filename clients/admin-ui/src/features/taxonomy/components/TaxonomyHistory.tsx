import { AntList, AntSkeleton } from "fidesui";
import { useGetTaxonomyHistoryQuery } from "~/features/taxonomy/taxonomy.slice";

const TaxonomyHistory = ({ taxonomyKey }: { taxonomyKey: string }) => {
  const { data, isLoading } = useGetTaxonomyHistoryQuery({
    fides_key: taxonomyKey,
  });
  if (isLoading) {
    return <AntSkeleton active />;
  }
  return (
    <AntList>
      {data?.items.map((item) => (
        <AntList.Item key={item.id}>
          <AntList.Item.Meta
            title={item.event_type}
            description={item.description}
          />
        </AntList.Item>
      ))}
    </AntList>
  );
};

export default TaxonomyHistory;
