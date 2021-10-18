# Fides Taxonomy Explorer

The taxonomy explorer is a useful way to visualize and review the taxonomy for those looking to explore in greater depth.

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap"
      rel="stylesheet"
    />
    

<div id="vis" class="vis vis-container">
  <div class="controls-container">
  
    <div id="data-control" class="control-group">
      <div class="btn-group">
        <button class="btn is-selected" data-chart-data="categories">Data Categories</button>
        <button class="btn" data-chart-data="uses">Data Uses</button>
        <button class="btn" data-chart-data="subjects">Data Subjects</button>
        <button class="btn" data-chart-data="qualifiers">Data Qualifiers</button>
      </div>
    </div>
    <div id="chart-type-control" class="control-group">
      <div class="btn-group">
        <button class="btn btn--icon is-selected" data-chart-type="tree">
          <img src="../../../img/Tree@1x.svg" alt="tree" />
        </button>
        <button class="btn btn--icon" data-chart-type="radialTree">
          <img src="../../../img/Radial%20Tree@1x.svg" alt="radial tree" />
        </button>
        <button class="btn btn--icon" data-chart-type="sunburst" >
          <img src="../../../img/Sunburst@1x.svg" alt="sunburst" />
        </button>
      </div>
    </div>
  </div>
  <div id="vis-chart" class="chart-container">
    <svg id="vis-sunburst"></svg>
    <svg id="vis-radial-tree"></svg>
    <svg id="vis-tree"></svg>
  </div>
  <div id="vis-color-legend"></div>
</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="../../../js/vis.js"></script>


