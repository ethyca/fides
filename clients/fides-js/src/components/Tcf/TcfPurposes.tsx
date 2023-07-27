import { h } from "preact";
import DataUseToggle from "../DataUseToggle";
import { PrivacyExperience } from "../../lib/consent-types";
import FilterButtons from "./FilterButtons";
import CookiesTable from "./CookiesTable";

const TcfPurposes = ({
  purposes,
}: {
  purposes: PrivacyExperience["tcf_purposes"];
}) => {
  if (!purposes) {
    return null;
  }
  const handleToggle = () => {};
  const firstDataUse = { key: `${purposes[0].id}`, name: purposes[0].name };
  const secondDataUse = { key: `${purposes[1].id}`, name: purposes[1].name };
  return (
    <div>
      <FilterButtons />
      <DataUseToggle dataUse={firstDataUse} checked onToggle={handleToggle}>
        <div style={{ padding: "0.5em" }}>
          <DataUseToggle
            dataUse={secondDataUse}
            checked
            onToggle={handleToggle}
            badge="gvl"
          >
            <div style={{ padding: "0.5em" }}>
              <p>
                Advertising presented to you on this service can be based on
                limited data, such as the website or app you are using, your
                non-precise location, your device type or which content you are
                (or have been) interacting with (for example, to limit the
                number of times an ad is presented to you).
              </p>
              <p className="fides-background-dark" style={{ padding: "0.5em" }}>
                A car manufacturer wants to promote its electric vehicles to
                environmentally conscious users living in the city after office
                hours. The advertising is presented on a page with related
                content (such as an article on climate change actions) after
                6:30 p.m. to users whose non-precise location suggests that they
                are in an urban zone.
              </p>
            </div>
          </DataUseToggle>
        </div>
      </DataUseToggle>
      <CookiesTable />
    </div>
  );
};

export default TcfPurposes;
