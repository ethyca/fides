class VisTree {
  constructor({ el, accessor, tooltip }) {
    this.el = el;
    this.accessor = accessor;
    this.tooltip = tooltip;
    this.resizeVis = this.resizeVis.bind(this);
    this.enteredNode = this.enteredNode.bind(this);
    this.movedNode = this.movedNode.bind(this);
    this.leftNode = this.leftNode.bind(this);
    this.init();
  }

  init() {
    this.dims = {
      margin: 0,
      nodeHeight: 48,
      nodeRadius: 3.5,
    };

    this.tree = d3
      .tree()
      .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

    this.svg = d3.select(this.el).attr("class", "tree-svg");
    this.g = this.svg.append("g");
    this.gLinks = this.g.append("g").attr("class", "links-g");
    this.gNodes = this.g.append("g").attr("class", "nodes-g");
    this.gLabels = this.g
      .append("g")
      .attr("class", "labels-g")
      .attr("fill", "currentColor");

    window.addEventListener("resize", this.resizeVis);
    this.resizeVis();
  }

  resizeVis() {
    if (this.svg.style("display") === "none") return;
    this.dims.width = this.el.parentNode.clientWidth;

    if (this.displayData) {
      this.wrangleData();
    }
  }

  renderVis() {
    this.renderLinks();
    this.renderNodes();
    this.renderNodeLabels();
    this.autoViewBox();
  }

  renderLinks() {
    this.link = this.gLinks
      .attr("fill", "none")
      .selectAll(".link")
      .data(this.displayData.links())
      .join((enter) => enter.append("path").attr("class", "link"))
      .attr("stroke", ({ target }) => {
        while (target.depth > 1) target = target.parent;
        return this.color(this.accessor.colorKey(target.data));
      })
      .attr(
        "d",
        d3
          .linkHorizontal()
          .x((d) => d.y)
          .y((d) => d.x)
      );
  }

  renderNodes() {
    this.node = this.gNodes
      .selectAll(".node")
      .data(
        this.displayData.descendants().filter((d) => d.depth !== 0),
        (d) => this.accessor.id(d.data)
      )
      .join((enter) =>
        enter
          .append("circle")
          .attr("class", "node")
          .attr("r", this.dims.nodeRadius)
          .attr("stroke", "transparent")
          .attr("stroke-width", 16)
          .on("mouseenter", this.enteredNode)
          .on("mousemove", this.movedNode)
          .on("mouseleave", this.leftNode)
      )
      .attr("transform", (d) => `translate(${d.y},${d.x})`)
      .attr("fill", (d) => {
        while (d.depth > 1) d = d.parent;
        return this.color(this.accessor.colorKey(d.data));
      });
  }

  renderNodeLabels() {
    this.labelText = this.gLabels
      .selectAll(".label-text")
      .data(
        this.displayData.descendants().filter((d) => d.depth !== 0),
        (d) => this.accessor.id(d.data)
      )
      .join((enter) =>
        enter
          .append("g")
          .attr("class", "label-text")
          .on("mouseenter", this.enteredNode)
          .on("mousemove", this.movedNode)
          .on("mouseleave", this.leftNode)
          .call((g) => g.append("text").attr("class", "label-text__bg"))
          .call((g) => g.append("text").attr("class", "label-text__fg"))
      );
    this.labelText
      .selectAll("text")
      .attr("transform", (d) => `translate(${d.y},${d.x})`)
      .attr("dy", "0.32em")
      .attr("x", (d) => (!d.children ? 6 : -6))
      .attr("text-anchor", (d) => (!d.children ? "start" : "end"))
      .text((d) => this.getLabelText(d));
  }

  enteredNode(event, d) {
    const ancestors = new Set(d.ancestors());
    this.link.classed("is-highlighted", ({ target }, i, n) => {
      if (ancestors.has(target)) {
        d3.select(n[i]).raise();
        return true;
      }
      return false;
    });
    this.node.classed("is-highlighted", (e) => ancestors.has(e));
    this.labelText.classed("is-highlighted", (e) => ancestors.has(e));
    this.tooltip.show({
      accessor: this.accessor,
      d,
    });
  }

  movedNode(event, d) {
    this.tooltip.move(event);
  }

  leftNode(event, d) {
    this.link.classed("is-highlighted", false);
    this.node.classed("is-highlighted", false);
    this.labelText.classed("is-highlighted", false);
    this.tooltip.hide();
  }

  autoViewBox() {
    const { x, y, width, height } = this.g.node().getBBox();

    this.svg.attr("viewBox", [
      width / 2 - this.dims.width / 2,
      Math.floor(y),
      this.dims.width,
      Math.ceil(height),
    ]);
  }

  wrangleData() {
    this.dims.nodeWidth =
      (this.dims.width - this.dims.margin * 2) / (this.root.height + 2);
    this.tree.nodeSize([this.dims.nodeHeight, this.dims.nodeWidth]);
    this.maxLetterCount = this.dims.nodeWidth / 6.5;
    this.displayData = this.tree(this.root);
    this.renderVis();
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
