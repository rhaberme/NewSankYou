var margin = { top: 30, right: 30, bottom: 30, left: 30};
var width = 1300; var height = 500;

first_run = true
function get_month(month_nr) {
    first_run = false
    switch (month_nr){
        case 0:
          data = input_data_object["TOT"];
          draw_sankey(data);
          break;
        case 1:
          data =  input_data_object["JAN"];
          draw_sankey(data);
          break;

        case 2:
          data =  input_data_object["FEB"];
                draw_sankey(data);

              break;
        case 3:
          data =  input_data_object["MAR"];
                draw_sankey(data);
              break;
        case 4:
          data =  input_data_object["APR"];
                draw_sankey(data);

              break;
        case 5:
          data =  input_data_object["MAY"];
                      draw_sankey(data);

              break;
        case 6:
          data =  input_data_object["JUN"];
                      draw_sankey(data);

              break;
        case 7:
          data =  input_data_object["JUL"];
                      draw_sankey(data);

              break;
        case 8:
          data =  input_data_object["AUG"];
                      draw_sankey(data);

              break;
        case 9:
          data =  input_data_object["SEP"];
                      draw_sankey(data);

              break;
        case 10:
          data =  input_data_object["OCT"];
          draw_sankey(data);

              break;
        case 11:
          data =  input_data_object["NOV"];
          draw_sankey(data);
          break;
        case 12:
          data =  input_data_object["DEC"];
          draw_sankey(data);
          break;
  }
  }


function draw_sankey(data) {
    chart_div = document.getElementById('chart');
    chart_div.innerHTML = ""
  var sankey = d3.sankeyCircular()
      .nodeWidth(10)
      .nodePadding(20) //can be overridden by nodePaddingRatio
      //.nodePaddingRatio(0.5)
      .size([width, height])
      .nodeId(function (d) {
        return d.name;
      })
      .nodeAlign(d3.sankeyJustify)
      .iterations(5)
      .circularLinkGap(1)
      .sortNodes("col")

  var svg = d3.select("#chart").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom);

  var g = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

  // todo nodes moveable
  // 1. https://bl.ocks.org/d3noob/3337957c360d55c245f6057ab0866c05
  // 2. https://bl.ocks.org/d3noob/5028304


  var linkG = g.append("g")
      .attr("class", "links")
      .attr("fill", "none")
      .attr("stroke-opacity", 0.5)
      .selectAll("path");

  var nodeG = g.append("g")
      .attr("class", "nodes")
      .attr("font-family", "sans-serif")
      .attr("font-size", 10)
      .selectAll("g");

  let sankeyData = sankey(data);
  let sankeyNodes = sankeyData.nodes;
  let sankeyLinks = sankeyData.links;

  let depthExtent = d3.extent(sankeyNodes, function (d) {
    return d.depth;
  });

  var nodeColour = d3.scaleSequential(d3.interpolateCool)
      .domain([0, width]);

  var node = nodeG.data(sankeyNodes)
      .enter()
      .append("g");

  node.append("rect")
      .attr("x", function (d) {
        return d.x0;
      })
      .attr("y", function (d) {
        return d.y0;
      })
      .attr("height", function (d) {
        return d.y1 - d.y0;
      })
      .attr("width", function (d) {
        return d.x1 - d.x0;
      })
      .style("fill", function (d) {
        return nodeColour(d.x0);
      })
      .style("opacity", 0.5)
      .on("mouseover", function (d) {

        let thisName = d.name;

        node.selectAll("rect")
            .style("opacity", function (d) {
              return highlightNodes(d, thisName)
            })

        d3.selectAll(".sankey-link")
            .style("opacity", function (l) {
              return l.source.name == thisName || l.target.name == thisName ? 1 : 0.3;
            })

        node.selectAll("text")
            .style("opacity", function (d) {
              return highlightNodes(d, thisName)
            })
      })
      .on("mouseout", function (d) {
        d3.selectAll("rect").style("opacity", 0.5);
        d3.selectAll(".sankey-link").style("opacity", 0.7);
        d3.selectAll("text").style("opacity", 1);
      })

  node.append("text")
      .attr("x", function (d) {
        return (d.x0 + d.x1) / 2;
      })
      .attr("y", function (d) {
        return d.y0 - 12;
      })
      // todo fix x and y position
      // https://stackoverflow.com/questions/35394461/d3-sankey-assign-fixed-x-y-position

      .attr("dy", "0.35em")
      .attr("text-anchor", "middle")
      .text(function (d) {
        return d.name;
      });

  node.append("title")
      .text(function (d) {
        return d.name + "\n" + (d.value);
      });

  var link = linkG.data(sankeyLinks)
      .enter()
      .append("g")
  link.append("path")
      .attr("class", "sankey-link")
      .attr("d", function (link) {
        return link.path;
      })
      .style("stroke-width", function (d) {
        return Math.max(1, d.width);
      })
      .style("opacity", 0.7)
      .style("stroke", function (link, i) {
        return link.circular ? "green" : "yellow"
          //link_color[link.source.name +"_"+ link.target.name] // todo

      })

  link.append("title")
      .text(function (d) {
        return d.source.name + " → " + d.target.name + "\n Index: " + (d.index);
      });

  function highlightNodes(node, name) {

    let opacity = 0.3

    if (node.name == name) {
      opacity = 1;
    }
    node.sourceLinks.forEach(function (link) {
      if (link.target.name == name) {
        opacity = 1;
      }
      ;
    })
    node.targetLinks.forEach(function (link) {
      if (link.source.name == name) {
        opacity = 1;
      }
      ;
    })

    return opacity;

  }
}

if (first_run) {
    get_month(0)}
