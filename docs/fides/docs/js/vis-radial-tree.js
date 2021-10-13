class VisRadialTree {
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
      margin: 80,
      maxHeight: 960,
      nodeRadius: 3.5,
    };
    this.maxLetterCount = this.dims.margin / 6.5;

    this.tree = d3
      .tree()
      .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

    this.svg = d3.select(this.el).attr("class", "radial-tree-svg");
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
    this.dims.height = Math.min(this.dims.width, this.dims.maxHeight);
    this.dims.radius =
      Math.min(this.dims.width, this.dims.height) / 2 - this.dims.margin;

    this.tree.size([2 * Math.PI, this.dims.radius]);

    if (this.displayData) {
      this.displayData = this.tree(this.root);
      this.renderVis();
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
          .linkRadial()
          .angle((d) => d.x)
          .radius((d) => d.y)
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
      .attr(
        "transform",
        (d) => `
        rotate(${(d.x * 180) / Math.PI - 90})
        translate(${d.y},0)
      `
      )
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
      .attr(
        "transform",
        (d) => `
        rotate(${(d.x * 180) / Math.PI - 90}) 
        translate(${d.y},0) 
        rotate(${d.x >= Math.PI ? 180 : 0})
      `
      )
      .attr("dy", "0.32em")
      .attr("x", (d) => (d.x < Math.PI === !d.children ? 6 : -6))
      .attr("text-anchor", (d) =>
        d.x < Math.PI === !d.children ? "start" : "end"
      )
      .text((d) => this.accessor.name(d.data));
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
    const { y, height } = this.g.node().getBBox();

    this.svg.attr("viewBox", [
      -this.dims.width / 2,
      Math.floor(y),
      this.dims.width,
      Math.ceil(height),
    ]);
  }

  wrangleData() {
    this.displayData = this.tree(this.root);
    this.renderVis();
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
