class VisSunburst {
  constructor({ el, accessor, tooltip }) {
    this.el = el;
    this.accessor = accessor;
    this.tooltip = tooltip;
    this.resizeVis = this.resizeVis.bind(this);
    this.enteredPartition = this.enteredPartition.bind(this);
    this.movedPartition = this.movedPartition.bind(this);
    this.leftPartition = this.leftPartition.bind(this);
    this.init();
  }

  init() {
    this.dims = {
      margin: 40,
      maxHeight: 960,
    };

    this.arc = d3
      .arc()
      .startAngle((d) => d.x0)
      .endAngle((d) => d.x1)
      .padAngle((d) => Math.min((d.x1 - d.x0) / 2, 0.005))
      .innerRadius((d) => d.y0)
      .outerRadius((d) => d.y1 - 1);

    this.partition = d3.partition();

    this.svg = d3.select(this.el).attr("class", "sunburst-svg");
    this.g = this.svg.append("g");
    this.gPartitions = this.g.append("g").attr("class", "partitions-g");
    this.gLabels = this.g
      .append("g")
      .attr("class", "labels-g")
      .attr("fill", "currentColor")
      .attr("pointer-events", "none")
      .attr("text-anchor", "middle");
    this.gCenter = this.g
      .append("g")
      .attr("class", "center-g")
      .call((g) => g.append("path").attr("class", "center-path"))
      .call((g) =>
        g
          .append("path")
          .attr("class", "center-text-path")
          .attr("fill", "none")
          .attr("id", "sunburst-center-text-path")
      )
      .call((g) =>
        g
          .append("text")
          .attr("class", "center-text")
          .attr("text-anchor", "middle")
          .attr("dy", "0.32em")
          .append("textPath")
          .attr("startOffset", "50%")
          .attr("xlink:href", "#sunburst-center-text-path")
      );

    window.addEventListener("resize", this.resizeVis);
    this.resizeVis();
  }

  resizeVis() {
    if (this.svg.style("display") === "none") return;
    this.dims.width = this.el.parentNode.clientWidth;
    this.dims.height = Math.min(this.dims.width, this.dims.maxHeight);
    this.dims.radius =
      Math.min(this.dims.width, this.dims.height) / 2 - this.dims.margin;

    this.arc.padRadius(this.dims.radius / 2);

    this.partition.size([2 * Math.PI, this.dims.radius]);

    if (this.displayData) {
      this.wrangleData();
    }
  }

  renderVis() {
    this.renderPartitionPaths();
    this.renderPartitionLabels();
    this.renderCenter();
    this.autoViewBox();
  }

  renderPartitionPaths() {
    this.partitionPath = this.gPartitions
      .selectAll(".partition-path")
      .data(this.displayData.descendants().filter((d) => d.depth))
      .join((enter) =>
        enter
          .append("path")
          .attr("class", "partition-path")
          .on("mouseenter", this.enteredPartition)
          .on("mousemove", this.movedPartition)
          .on("mouseleave", this.leftPartition)
      )
      .attr("fill", (d) => {
        while (!this.color.domain().includes(this.accessor.colorKey(d.data)))
          d = d.parent;
        return this.color(this.accessor.colorKey(d.data));
      })
      .attr("d", this.arc);
  }

  renderPartitionLabels() {
    this.labelText = this.gLabels
      .selectAll(".label-text")
      .data(
        this.displayData
          .descendants()
          .filter((d) => d.depth && ((d.y0 + d.y1) / 2) * (d.x1 - d.x0) > 10)
      )
      .join((enter) =>
        enter.append("text").attr("class", "label-text").attr("dy", "0.35em")
      )
      .attr("fill", "#ffffff")
      .attr("transform", function (d) {
        const x = (((d.x0 + d.x1) / 2) * 180) / Math.PI;
        const y = (d.y0 + d.y1) / 2;
        return `rotate(${
          x - 90
        }) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
      })
      .text((d) => this.getLabelText(d));
  }

  renderCenter() {
    this.gCenter
      .select(".center-path")
      .attr("fill", this.color(this.accessor.colorKey(this.displayData)))
      .attr(
        "d",
        this.arc({
          x0: -Math.PI,
          x1: Math.PI,
          y0: this.displayData.y1 - this.dims.margin,
          y1: this.displayData.y1,
        })
      );

    this.gCenter.select(".center-text-path").attr("d", () => {
      const r = this.displayData.y1 - this.dims.margin / 2;
      const startAngle = (-Math.PI * 3) / 2 + 0.001;
      const endAngle = Math.PI / 2 - 0.001;
      const x0 = r * Math.cos(startAngle);
      const y0 = r * Math.sin(startAngle);
      const x1 = r * Math.cos(endAngle);
      const y1 = r * Math.sin(endAngle);
      return `M ${x0} ${y0} A ${r} ${r} 0 1 1 ${x1} ${y1}`;
    });

    this.gCenter
      .select(".center-text textPath")
      .attr("fill", "#ffffff")
      .text(this.displayData.data.name);
  }

  enteredPartition(event, d) {
    const ancestors = new Set(d.ancestors());
    this.partitionPath.classed("is-highlighted", (e) => ancestors.has(e));
    this.labelText.classed("is-highlighted", (e) => ancestors.has(e));
    this.tooltip.show({
      accessor: this.accessor,
      d,
    });
  }

  movedPartition(event, d) {
    this.tooltip.move(event);
  }

  leftPartition(event, d) {
    this.partitionPath.classed("is-highlighted", false);
    this.labelText.classed("is-highlighted", false);
    this.tooltip.hide();
  }

  wrangleData() {
    this.root.count().sort((a, b) => b.value - a.value);
    this.displayData = this.partition(this.root);
    this.displayData.each((d) => {
      if (d.y0 < 0) {
        d.y0 -= this.dims.margin;
      } else {
        d.y0 += this.dims.margin;
      }
      if (d.y1 < 0) {
        d.y1 -= this.dims.margin;
      } else {
        d.y1 += this.dims.margin;
      }
    });
    this.maxLetterCount = (this.displayData.y1 - this.displayData.y0) / 6.5;
    this.renderVis();
  }

  autoViewBox() {
    const { y, height } = this.g.node().getBBox();

    this.svg.attr("viewBox", [
      -this.dims.width / 2,
      Math.floor(y),
      this.dims.width,
      Math.ceil(height),
    ]);
  }

  getLabelText(d) {
    let label = this.accessor.name(d.data);
    if (label.length > this.maxLetterCount) {
      if (!d.children) {
        label = "..." + label.slice(label.length - this.maxLetterCount + 2);
      } else {
        label = label.slice(0, this.maxLetterCount - 1) + "...";
      }
    }
    return label;
  }

  destroy() {
    window.removeEventListener("resize", this.resizeVis);
    this.svg.selectAll("*").remove();
  }

  updateData({ data, color }) {
    this.root = data;
    this.color = color;
    this.wrangleData();
  }
}
