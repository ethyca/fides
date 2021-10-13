class VisColorLegend {
  constructor({ el }) {
    this.el = el;
  }

  renderLegend() {
    d3.select(this.el)
      .classed("vis-color-legend", true)
      .selectAll(".legend-item")
      .data(this.scale.domain())
      .join((enter) =>
        enter
          .append("div")
          .attr("class", "legend-item")
          .call((item) => item.append("div").attr("class", "legend-swatch"))
          .call((item) => item.append("div").attr("class", "legend-label"))
      )
      .call((item) =>
        item
          .select(".legend-swatch")
          .style("background-color", (d) => this.scale(d))
      )
      .call((item) => item.select(".legend-label").text((d) => d));
  }

  updateScale(scale) {
    this.scale = scale;
    this.renderLegend();
  }
}
