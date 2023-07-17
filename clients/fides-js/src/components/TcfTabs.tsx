import { h } from "preact";
import { useRef, useState } from "preact/hooks";

const TCF_TABS = [
  { name: "Purposes", content: "one" },
  { name: "Features", content: "two" },
  { name: "Vendors", content: "three" },
];

const KEY_ARROW_RIGHT = "ArrowRight";
const KEY_ARROW_LEFT = "ArrowLeft";

const TcfTabs = () => {
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const inputRefs = [
    useRef<HTMLButtonElement>(null),
    useRef<HTMLButtonElement>(null),
    useRef<HTMLButtonElement>(null),
  ];
  const handleKeyDown = (event: KeyboardEvent) => {
    let newActiveTab;
    if (event.code === KEY_ARROW_RIGHT) {
      event.preventDefault();
      newActiveTab =
        activeTabIndex === TCF_TABS.length - 1 ? 0 : activeTabIndex + 1;
    }
    if (event.code === KEY_ARROW_LEFT) {
      event.preventDefault();
      newActiveTab =
        activeTabIndex === 0 ? TCF_TABS.length - 1 : activeTabIndex - 1;
    }
    if (newActiveTab != null) {
      setActiveTabIndex(newActiveTab);
      inputRefs[newActiveTab].current?.focus();
    }
  };
  return (
    <div className="fides-tabs">
      <ul role="tablist" className="fides-tab-list">
        {TCF_TABS.map(({ name }, idx) => (
          <li role="presentation" key={name}>
            <button
              id={`fides-tab-${name}`}
              aria-selected={idx === activeTabIndex}
              onClick={() => {
                setActiveTabIndex(idx);
              }}
              role="tab"
              type="button"
              className="fides-tab-button"
              tabIndex={idx === activeTabIndex ? undefined : -1}
              onKeyDown={handleKeyDown}
              ref={inputRefs[idx]}
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
            tabIndex={-1}
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
export default TcfTabs;
