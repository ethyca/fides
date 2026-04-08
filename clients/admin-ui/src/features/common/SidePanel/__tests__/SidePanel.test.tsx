import React from "react";

import SidePanel from "../SidePanel";

describe("SidePanel", () => {
  it("attaches all slot sub-components", () => {
    expect(SidePanel.Identity).toBeDefined();
    expect(SidePanel.Navigation).toBeDefined();
    expect(SidePanel.Search).toBeDefined();
    expect(SidePanel.Actions).toBeDefined();
    expect(SidePanel.Filters).toBeDefined();
    expect(SidePanel.ViewSettings).toBeDefined();
    expect(SidePanel.SavedViews).toBeDefined();
  });

  it("has correct slotOrder on each sub-component", () => {
    expect(SidePanel.Identity.slotOrder).toBe(0);
    expect(SidePanel.Navigation.slotOrder).toBe(1);
    expect(SidePanel.Search.slotOrder).toBe(2);
    expect(SidePanel.Actions.slotOrder).toBe(3);
    expect(SidePanel.Filters.slotOrder).toBe(4);
    expect(SidePanel.ViewSettings.slotOrder).toBe(5);
    expect(SidePanel.SavedViews.slotOrder).toBe(6);
  });

  it("auto-sort logic: children sorted by slotOrder", () => {
    // Simulate what useSidePanelSlots does
    const children = [
      <SidePanel.Actions key="a">
        <button type="button">Add</button>
      </SidePanel.Actions>,
      <SidePanel.Identity key="b" title="Test" />,
      <SidePanel.Search key="c" onSearch={() => {}} />,
    ];

    const sorted = React.Children.toArray(children)
      .filter(React.isValidElement)
      .sort((a, b) => {
        const orderA = (a.type as any).slotOrder ?? 99;
        const orderB = (b.type as any).slotOrder ?? 99;
        return orderA - orderB;
      });

    expect(sorted).toHaveLength(3);
    // Identity (0) first, Search (2) second, Actions (3) third
    expect((sorted[0].type as any).slotOrder).toBe(0);
    expect((sorted[1].type as any).slotOrder).toBe(2);
    expect((sorted[2].type as any).slotOrder).toBe(3);
  });
});
