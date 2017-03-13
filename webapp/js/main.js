'use strict';

window.constants = {
   // We serve the client and api from the same server.
   baseURL: '',
   maxDisplayNameLength: 30,

   // Layout configuration.
   nodeWidth: 80,
   nodeHeight: 80,
   verticalPadding: 150,
   innerMargin: 100, // Space between terminal nodes and inner area.
   innerWidth: 1000,

   // Edge colors.
   edgeColorOutter: '#03b7b7', // Teal
   edgeColorStrong: '#39e512', // Green
   edgeColorMedStrong: '#c8ed25', // Yellow-Green
   edgeColorMedWeak: '#efec26', // Yellow
   edgeColorWeak: '#e82910', // Red

   // Animation settings.
   animate: true,
   animationDurationMS: 2000,
   panXOffset: 90,
   zoom: 0.85,
   panY: 200,
   easing: 'spring(500, 20)',

   // Misc
   straightLines: false,
};

function fetchEntities() {
   var targetUrl = window.constants.baseURL + '/api/entities';

   waitingDialog.show('One sec... loading entities from server.');

   $.get(targetUrl, function(data) {
      console.log("Got entities");

      // {facebookId: id, ...}
      var idMap = {}

      var sourceList = document.getElementById('source-list');
      var targetList = document.getElementById('target-list');

      for (var key in data) {
         var option = document.createElement('option');
         // Display name
         option.text = data[key][1].substring(0, window.constants.maxDisplayNameLength);

         // Facebook id
         option.value = data[key][0];

         // Internal id.
         idMap[data[key][0]] = key;

         // People are sources, everything else is targets.
         if (data[key][2]) {
            sourceList.appendChild(option);
         } else {
            targetList.appendChild(option);
         }
      }

      window.constants.idMap = idMap;

      waitingDialog.hide();
   });
}

function fetchPaths(startId, endId, numPaths) {
   var targetUrlBase = window.constants.baseURL + '/api/path';
   var targetUrl = targetUrlBase + '/' + startId + '/' + endId + '/' + numPaths;

   waitingDialog.show('Searching for paths ...');
   $.get(targetUrl, function(data) {
      console.log("Got data, loading graph.");
      console.log(data);

      loadGraph(data);
      waitingDialog.hide();
   });
}

function findConnections() {
   var sourceValue = document.getElementById('source-input').value;
   var targetValue = document.getElementById('target-input').value;
   var numPaths = document.getElementById('num-paths').value;

   if (!sourceValue || !targetValue || !numPaths) {
      alert("Need to specify all three values: source, target, and number of paths.");
      return;
   }

   var startId = window.constants.idMap[sourceValue];
   var endId = window.constants.idMap[targetValue];

   if (!startId || !endId) {
      console.error("Failed to get internal ids for targets.");
      return;
   }

   fetchPaths(startId, endId, numPaths);
}

// It is possible for an entity to appear in multiple paths.
// So, we need to give all unique identifiers.
// We need to translate the paths using these identifiers and return a mapping of the new identifiers to nodes.
// Returns: [{newId: nodeId, ...}, [[translated path], ...]]
function translatePaths(paths) {
   var nodeIdMap = {};
   var cytoscapePaths = [];

   var count = 0;
   paths.forEach(function(path, pathIndex) {
      var cytoscapePath = [];

      path.forEach(function(node, i) {
         var id = '' + count;
         count++;

         nodeIdMap[id] = node;
         cytoscapePath.push(id);
      });

      cytoscapePaths.push(cytoscapePath);
   });

   return [nodeIdMap, cytoscapePaths];
}

// Format the nodes, edges,and paths to how cytoscape likes it.
// Returns: {nodes: nodes, edges: edges, paths: paths}.
function formatCytoscapeInfo(pathsInfo) {
   var cytoscapeNodes = [];
   var cytoscapeEdges = [];

   var nodeTranslationInfo = translatePaths(pathsInfo.paths);
   var nodeIdMap = nodeTranslationInfo[0];
   var cytoscapePaths = nodeTranslationInfo[1];

   for (var nodeId in nodeIdMap) {
      var background = 'none';
      if (pathsInfo.nodes[nodeIdMap[nodeId]][3]) {
         background = 'url(data:image/gif;base64,' + pathsInfo.nodes[nodeIdMap[nodeId]][3] + ')';
      }

      cytoscapeNodes.push({
         data: {
            id: nodeId,
            label: pathsInfo.nodes[nodeIdMap[nodeId]][1],
            image: background
         }
      });
   }

   cytoscapePaths.forEach(function(path) {
      for (var i = 0; i < path.length - 1; i++) {
         // Non-cytoscape ids.
         var startId = nodeIdMap[path[i]];
         var endId = nodeIdMap[path[i + 1]];
         var outter = i == (path.length - 2) ? true : false;

         cytoscapeEdges.push({
            data: {
               id: '' + path[i] + '-' + path[i + 1],
               weight: pathsInfo.edgeInfo[startId][endId],
               source: path[i],
               target: path[i + 1],
               outter: outter
            }
         });
      }
   });

   return {
      'nodes': cytoscapeNodes,
      'edges': cytoscapeEdges,
      'paths': cytoscapePaths
   };
}

function loadGraph(pathsInfo) {
   var stylesheet = cytoscape.stylesheet()
      .selector('node')
         .css({
            'height': window.constants.nodeHeight,
            'width': window.constants.nodeWidth,
            'shape': 'roundrectangle',
            'label': 'data(label)',
            'text-valign': 'bottom',
            'background-fit': 'cover',
            'border-color': '#000',
            'border-width': 3,
            'border-opacity': 0.5
         })
      .selector('.eating')
         .css({
            'border-color': 'red'
         })
      .selector('.eater')
         .css({
            'border-width': 9
         })
      .selector('edge')
         .css({
            'width': 5,
            'target-arrow-shape': 'triangle',
            // 'line-color': 'mapData(weight, 0, 1, green, red)',
            // 'target-arrow-color': 'mapData(weight, 0, 1, green, red)',
            'line-color': edgeColor,
            'target-arrow-color': edgeColor,
            'curve-style': window.constants.straightLines ? 'bezier' : 'unbundled-bezier'
         })
      .selector('node')
         .css({
            'background-image': 'data(image)'
         })
   ;

   var cytoscapeInfo = formatCytoscapeInfo(pathsInfo);
   var layoutPositions = getPositions(cytoscapeInfo.paths);

   // We need the max height for proper dimensions.
   var maxHeight = -1;
   for (var key in layoutPositions) {
      if (maxHeight < layoutPositions[key].y) {
         maxHeight = layoutPositions[key].y;
      }
   }

   // Force the vertial size of the viewport.
   $('#graph-area').height(maxHeight + window.constants.panY * 2);

   var options = {
      container: document.getElementById('graph-area'),
      boxSelectionEnabled: false,
      userZoomingEnabled: false,
      userPanningEnabled: false,
      autounselectify: true,
      style: stylesheet,
      elements: {
         nodes: cytoscapeInfo.nodes,
         edges: cytoscapeInfo.edges,
      },
      layout: {
         name: 'preset',
         padding: 30,
         fit: true,
         positions: layoutPositions
      }
   };

   // Add in some additional options if we are animating.
   if (window.constants.animate) {
      var initialPositions = {};
      for (var key in layoutPositions) {
         initialPositions[key] = {
            x: window.constants.nodeWidth / 2 + window.constants.innerMargin + window.constants.innerWidth / 2,
            y: window.constants.verticalPadding
         };
      }

      var graphAreaWidth = window.constants.nodeWidth + (2 * window.constants.innerMargin) + window.constants.innerWidth;
      var panX = ($('#graph-area').width() - graphAreaWidth) / 2 + window.constants.panXOffset;

      options['zoom'] = window.constants.zoom;
      options['pan'] = {
         x: panX,
         y: window.constants.panY,
      };

      options.layout.fit = false;
      options.layout.positions = initialPositions;
   }

   var cy = cytoscape(options);

   if (window.constants.animate) {
      cy.nodes().forEach(function(node) {
         node.animate({
            position: layoutPositions[node.data('id')],
            duration: window.constants.animationDurationMS,
            easing: window.constants.easing,
         });
      });
   }
}

function edgeColor(edge) {
   var weight = edge.data('weight');
   var outter = edge.data('outter');

   if (outter) {
      return window.constants.edgeColorOutter;
   } else if (weight <= 0.25) {
      return window.constants.edgeColorStrong;
   } else if (weight <= 0.50) {
      return window.constants.edgeColorMedStrong;
   } else if (weight <= 0.75) {
      return window.constants.edgeColorMedWeak;
   } else {
      return window.constants.edgeColorWeak;
   }
}

function getPositions(paths) {
   var innerOffset = window.constants.innerMargin + (window.constants.nodeWidth / 2); // Space before actual start of the inner area.
   var innerEnd = innerOffset + window.constants.innerWidth;

   var positions = {};

   paths.forEach(function(path, pathIndex) {
      var yPosition = pathIndex * window.constants.verticalPadding;

      // Layout the terminal nodes.
      positions[path[0]] = {x: 0, y: yPosition};
      positions[path[path.length - 1]] = {x: innerEnd + innerOffset, y: yPosition};

      // Cut off the terminal nodes for simplicity.
      var nodes = path.slice(1, path.length - 1);

      // Evenly space all nodes in the path.
      var nodeSpacing = window.constants.innerWidth / (nodes.length + 1);

      nodes.forEach(function(node, i) {
         var xPosition = innerOffset + ((i + 1) * nodeSpacing);
         positions[node] = {x: xPosition, y: yPosition};
      });
   });

   return positions;
}

$(document).ready(function() {
   fetchEntities();
});
