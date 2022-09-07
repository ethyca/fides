

var VisColorLegend = class VisColorLegend {
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

var VisTooltip = class VisTooltip {
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

var VisSunburst = class VisSunburst {
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


var VisRadialTree = class VisRadialTree {
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
var VisTree = class VisTree {
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
    return this.accessor.name(d.data);
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


Promise.all([
  d3.csv("../../../csv/data_categories.csv"),
  d3.csv("../../../csv/data_uses.csv"),
  d3.csv("../../../csv/data_subjects.csv"),
  d3.csv("../../../csv/data_qualifiers.csv"),
]).then(([categoriesCSV, usesCSV, subjectsCSV, qualifiersCSV]) => {
  const tooltip = new VisTooltip();

  const colors = {
    categories: d3
      .scaleOrdinal()
      .domain([
        "Data Category",
        "System Data",
        "User Data",
        "User Provided Data",
        "Account Data",
        "Derived Data",
      ])
      .range([
        "#0861ce",
        "#8459cc",
        "#c14cbb",
        "#ed43a0",
        "#ff4a7f",
        "#ffa600",
      ]),
    uses: d3
      .scaleOrdinal()
      .domain([
        "Data Use",
        "Provide the capability",
        "Improve the capability",
        "Personalize the capability",
        "Advertising, Marketing or Promotion",
        "Third Party Sharing",
        "Collect",
        "Train AI System",
      ])
      .range([
        "#0861ce",
        "#8459cc",
        "#c14cbb",
        "#ed43a0",
        "#ff4a7f",
        "#ff635b",
        "#ff8436",
        "#ffa600",
      ]),
    subjects: d3
      .scaleOrdinal()
      .domain([
        "Data Subject",
        "Anonymous User",
        "Citizen Voter",
        "Commuter",
        "Consultant",
        "Custom",
        "Employee",
        "Job Applicant",
        "Next of Kin",
        "Passenger",
        "Patient",
        "Prospect",
        "Shareholder",
        "Supplier/Vendor",
        "Trainee",
        "Visitor",
      ])
      .range([
        "#0861ce",
        "#ff7040",
        "#ffa040",
        "#ffcf40",
        "#acff40",
        "#58ff40",
        "#52cf70",
        "#4ca0a0",
        "#4670cf",
        "#4040ff",
        "#6e40fe",
        "#9c40fe",
        "#c93ffd",
        "#f73ffc",
        "#fb409e",
        "#fd406f",
      ]),
    qualifiers: d3
      .scaleOrdinal()
      .domain([
        "Data Qualifier",
        "Identified Data",
        "Pseudonymized Data",
        "Unlinked Pseudonymized Data",
        "Anonymized Data",
        "Aggregated Data",
      ])
      .range([
        "#0861ce",
        "#8459cc",
        "#c14cbb",
        "#ed43a0",
        "#ff4a7f",
        "#ffa600",
      ]),
  };

  const elColorLegend = document.querySelector("#vis-color-legend");

  const colorLegend = new VisColorLegend({
    el: elColorLegend,
  });

  const accessor = {
    id: (d) => d.fides_key,
    parentId: (d) => d.parent_key,
    name: (d) =>
      d.fides_key
        .slice(d.fides_key.lastIndexOf(".") + 1)
        .split("_")
        .map((d) => d[0].toUpperCase() + d.slice(1))
        .join(" "),
    colorKey: (d) => d.name,
    description: (d) => d.description,
  };

  const stratify = d3.stratify().id(accessor.id).parentId(accessor.parentId);

  // Chart data control
  const categoriesRoot = stratify(categoriesCSV);
  const usesRoot = stratify(usesCSV);
  const subjectsRoot = stratify(subjectsCSV);
  const qualifiersRoot = stratify(qualifiersCSV);

  const chartData = {
    categories: categoriesRoot,
    uses: usesRoot,
    subjects: subjectsRoot,
    qualifiers: qualifiersRoot,
  };
  const chartDataButtons = d3
    .select("#data-control")
    .selectAll("button")
    .on("click", (event) => {
      chartDataButtons.classed("is-selected", function () {
        return this === event.currentTarget;
      });
      selected.chartData = event.currentTarget.dataset.chartData;
      const data = chartData[selected.chartData].copy();
      const color = colors[selected.chartData].copy();
      colorLegend.updateScale(color);
      chart[selected.chartType].updateData({
        data,
        color,
      });
    });

  // Chart type control
  
  
  const chartType = {
    sunburst: {
      chart: VisSunburst,
      el: document.querySelector("#vis-sunburst"),
    },
    radialTree: {
      chart: VisRadialTree,
      el: document.querySelector("#vis-radial-tree"),
    },
    tree: {
      chart: VisTree,
      el: document.querySelector("#vis-tree"),
    },
  };

  const chart = {};
  const chartTypeButtons = d3
    .select("#chart-type-control")
    .selectAll("button")
    .on("click", (event) => {
      chartTypeButtons.classed("is-selected", function () {
        return this === event.currentTarget;
      });
      selected.chartType = event.currentTarget.dataset.chartType;
      for (const property in chartType) {
        chartType[property].el.style.display =
          property === selected.chartType ? "block" : "none";
      }
      if (!chart[selected.chartType]) {
        chart[selected.chartType] = new chartType[selected.chartType].chart({
          el: chartType[selected.chartType].el,
          accessor,
          tooltip,
        });
      }
      const data = chartData[selected.chartData].copy();
      const color = colors[selected.chartData].copy();
      colorLegend.updateScale(color);
      chart[selected.chartType].updateData({
        data,
        color,
      });
    });

  // Init
  const selected = {
    chartType: chartTypeButtons
      .filter(function () {
        return this.classList.contains("is-selected");
      })
      .node().dataset.chartType,
    chartData: chartDataButtons
      .filter(function () {
        return this.classList.contains("is-selected");
      })
      .node().dataset.chartData,
  };
  chartTypeButtons
    .filter(function () {
      return this.classList.contains("is-selected");
    })
    .node()
    .click();
});
