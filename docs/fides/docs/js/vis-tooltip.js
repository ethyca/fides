class VisTooltip {
  constructor() {
    this.tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "vis vis-tooltip");
    this.show = this.show.bind(this);
    this.hide = this.hide.bind(this);
    this.move = this.move.bind(this);
  }

  show({ accessor, d }) {
    const content = `
    <div class="card">
      <div class="card-title">${accessor.name(d.data)}</div>
      <div>
        <div class="card-subtitle">Hierarchy:</div>
        <div style="text-transform: capitalize">${accessor
          .id(d.data)
          .split(".")
          .map((d) => d.replace(/_/g, " "))
          .join(" > ")}</div>
      </div>
      ${
        accessor.description(d.data)
          ? `<div>
              <div class="card-subtitle">Description:</div>
              <div>${accessor.description(d.data)}</div>
            </div>`
          : ""
      }
    </div>
    `;
    this.tooltip.html(content).classed("is-visible", true);
    const box = this.tooltip.node().getBoundingClientRect();
    this.width = box.width;
    this.height = box.height;
  }

  hide() {
    this.tooltip.classed("is-visible", false);
  }

  move(event) {
    const padding = 16;
    let x = event.pageX;
    let y = event.pageY;
    const bodyWidth = document.body.clientWidth;
    const bodyHeight = document.body.clientHeight;
    if (x < bodyWidth / 2) {
      x = x - this.width - padding;
      if (x < 0) {
        x = 0;
      }
    } else {
      x = x + padding;
      if (x + this.width > bodyWidth) {
        x = bodyWidth - this.width;
      }
    }
    if (y < bodyHeight / 2) {
      y = y - this.height - padding;
      if (y < 0) {
        y = 0;
      }
    } else {
      y = y + padding;
      if (y + this.height > bodyHeight) {
        y = bodyHeight - this.height;
      }
    }

    this.tooltip.style("transform", `translate(${x}px,${y}px)`);
  }
}
