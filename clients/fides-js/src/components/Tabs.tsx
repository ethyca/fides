import { h, JSX } from "preact";

type ButtonAttrs = JSX.IntrinsicElements["button"];

const TabButton = ({ children, ...props }: ButtonAttrs) => (
  <button role="tab" type="button" className="fides-tab-button" {...props}>
    {children}
  </button>
);

const Tabs = () => (
  <div className="fides-tabs">
    <ul role="tablist" className="fides-tab-list">
      <li role="presentation">
        <TabButton id="tab1" aria-selected="true">
          Tab one
        </TabButton>
      </li>
      <li role="presentation">
        <TabButton id="tab2">Tab two</TabButton>
      </li>
      <li role="presentation">
        <TabButton id="tab3">Tab three</TabButton>
      </li>
      <li role="presentation">
        <TabButton id="tab4">Tab four</TabButton>
      </li>
    </ul>
    <div className="tabpanel-container">
      <section role="tabpanel" id="panel1" aria-labelledby="tab1" tabIndex={0}>
        one
      </section>
      <section
        role="tabpanel"
        id="panel2"
        aria-labelledby="tab2"
        tabIndex={0}
        hidden
      >
        two
      </section>
      <section
        role="tabpanel"
        id="panel3"
        aria-labelledby="tab3"
        tabIndex={0}
        hidden
      >
        three
      </section>
      <section
        role="tabpanel"
        id="panel4"
        aria-labelledby="tab4"
        tabIndex={0}
        hidden
      >
        four
      </section>
    </div>
  </div>
);

export default Tabs;
