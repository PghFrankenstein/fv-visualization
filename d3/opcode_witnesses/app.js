(function () {

  var witnesses = [
    "f1818", "f1823", "f1831", "fThomas"
  ]

  var source_witness = "f1818"
  var diff_type = "balance"

  function get_source_witness() {
    return source_witness
  };

  function set_source_witness(id) {
    source_witness = id
    return true
  };

  function get_diff_type() {
    return diff_type
  }

  function set_diff_type(type) {
    diff_type = type
    return true
  }

  function draw_apps(data) {
    var maxNchar = data.stats.nchar.max
    var width_scale = d3.scale.linear().domain([0, maxNchar]).range([0, 200])

    var minadd = data.stats.addition.min
    var maxadd = data.stats.addition.max
    var mindel = data.stats.deletion.min
    var maxdel = data.stats.deletion.max
    var mincombo = data.stats.balance.min
    var maxcombo = data.stats.balance.max

    var add_scale = d3.scaleSequential(d3.interpolateOranges).domain([minadd, maxadd])
    var del_scale = d3.scaleSequential(d3.interpolatePurples).domain([mindel, maxdel])
    var mincombo = data.stats.balance.min
    var mag_scale = d3.scaleDiverging(d3.interpolatePuOr).domain([mincombo, 0, maxcombo])
    var agg_scale = d3.scale.linear().domain([0, 1]).range([0.2, 1])

    function diff_scale(type) {
      if (type == "additions") {
        return add_scale
      } else if (type == "deletions") {
        return del_scale
      } else if (type == "balance") {
        return mag_scale
      }
    }

    function entries(obj) {
      for (key in Object.keys(obj)) {
        return [key, obj[key]];
      }
    }

    function witness_shift(base_witness, reference_witness, difftype) {
      if (base_witness == reference_witness) {
        d3.select(".wrapper#" + base_witness)
          .selectAll("div.app")
          .transition()
          .duration(2000)
          .style("background-color", d => diff_scale(difftype)(d3.mean(Object.values(d[base_witness].diffs), v => v.stats[difftype])))
      } else {
        d3.select(".wrapper#" + base_witness)
          .selectAll("div.app")
          .transition()
          .duration(2000)
          .style("background-color", d => diff_scale(difftype)(d[base_witness].diffs[reference_witness].stats[difftype]))
      }
    }

    function witness_button_click() {
      var wit_id = this.getAttribute("id")
      d3.selectAll("div.witness-col")
        .classed("hovered", false)
      d3.select("div.witness-col#" + wit_id)
        .classed("hovered", true)
      set_source_witness(wit_id)
      d3.selectAll("button.witness-button")
        .classed("active", false)
      this.classList.add("active")
      for (i = 0; i < witnesses.length; i++) {
        witness_shift(witnesses[i], get_source_witness(), get_diff_type())
      }
    }

    function diff_button_click() {
      set_diff_type(this.getAttribute("id"))
      d3.selectAll("button.diff-button")
        .classed("active", false)
      this.classList.add("active")
      for (i = 0; i < witnesses.length; i++) {
        witness_shift(witnesses[i], get_source_witness(), get_diff_type())
      }
    }

    function truncate_string(s, max) {
      if (s == null) {
        return ""
      }
      if (s.length > max) {
        return s.substring(0, max) + "..."
      } else {
        return s
      }
    }

    function app_hover(d) {
      d3.selectAll("div.app#" + d.seg)
        .classed("hovered", true)
      for (i = 0; i < witnesses.length; i++) {
        d3.select("p.text-display#" + witnesses[i])
          .text(d.seg + ": " + d[witnesses[i]].text.content)
      }
    }

    function app_nohover(d) {
      d3.selectAll("div.app#" + d.seg)
        .classed("hovered", false)
    };

    d3.selectAll("button.witness-button")
      .on("click", witness_button_click);

    d3.selectAll("button.diff-button")
      .on("click", diff_button_click);

    for (i = 0; i < witnesses.length; i++) {
      d3.select(".wrapper#" + witnesses[i])
        .selectAll("div.app")
        .data(data.segs)
        .enter()
        .append("div")
        .classed("app", true)
        .classed("hidden", d => d[witnesses[i]].text.nchar <= 0)
        .attr("id", d => d.seg)
        .style("width", d => width_scale(d[witnesses[i]].text.nchar) + "px");

      witness_shift(witnesses[i], get_source_witness(), get_diff_type());
    }

    d3.selectAll("div.app")
      .on("mouseover", app_hover)
      .on("mouseout", app_nohover)
  }

  d3.json("diffs.json", function (error, data) {
    if (error) {
      console.error(error)
    } else {
      draw_apps(data)
    }
  })

})();
