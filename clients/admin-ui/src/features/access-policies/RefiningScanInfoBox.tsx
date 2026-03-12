import { Card, Icons } from "fidesui";

interface RefiningScanInfoBoxProps {
  industry: string | null;
}

const RefiningScanInfoBox = ({ industry }: RefiningScanInfoBoxProps) => {
  const industryLabel = industry
    ? industry.charAt(0).toUpperCase() + industry.slice(1)
    : "your";

  return (
    <Card>
      <div className="flex gap-3">
        <Icons.Information size={20} className="mt-0.5 shrink-0" />
        <div>
          <div className="mb-1 text-sm font-semibold">Refining the scan</div>
          <div className="text-sm text-neutral-7">
            These parameters help Fides focus its scanning engine on the most
            relevant signals for {industryLabel} environments. The selections
            above are used to auto-generate an initial draft of your access
            governance policies.
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RefiningScanInfoBox;
