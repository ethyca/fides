import { h } from "preact";

const TCF_TABS = [
  { name: "Purposes", content: "one" },
  { name: "Features", content: "two" },
  { name: "Vendors", content: "three" },
];

const Tabs = () => {
  // TODO useState, but that doesn't work with cypress component tests yet...
  const activeTabIndex = 1;
  return (
    <div className="fides-tabs">
      <ul role="tablist" className="fides-tab-list">
        {TCF_TABS.map(({ name }, idx) => (
          <li role="presentation" key={name}>
            <button
              id={`fides-tab-${name}`}
              aria-selected={idx === activeTabIndex}
              //   onClick={() => {
              //     setActiveTabIndex(idx);
              //   }}
              role="tab"
              type="button"
              className="fides-tab-button"
            >
              {name}
            </button>
          </li>
        ))}
      </ul>
      <div className="tabpanel-container">
        {TCF_TABS.map(({ name, content }, idx) => (
          <section
            role="tabpanel"
            id={`fides-panel-${name}`}
            aria-labelledby={`fides-tab-${name}`}
            tabIndex={0}
            hidden={idx !== activeTabIndex}
            key={name}
          >
            {content}
          </section>
        ))}
      </div>
    </div>
  );
};
export default Tabs;
