const d3 = require('d3');
const d3tip = require('d3-tip');
if (!d3.tip) {
    d3.tip = d3tip;
}

var EtsGraph = class {
    constructor (data, boundingBoxId) {
        this._graphData = data;
        this._boundingBox = document.getElementById(boundingBoxId);
    }

    /**
    Renders the d3 tree after it has been built.
    @method render
    **/
    render () {
        let data = this.getData();
        this._tree = this._createTree(data);
        this._toolTip = this._createToolTip();
        this._updateTree(this.getRoot());
    }

    // destroy () {
    //     this._tree
    // }

    /**
    Builds the d3 tree and all its parts.
    @method _createTree
    @param {Object} data
    @return tree
    @private
    **/
    _createTree (data) {
        const bb = this._boundingBox;
        const height = bb.offsetHeight;
        const width = bb.offsetWidth;
        const tree = d3.layout.tree().size([height, width]);

        this._setDiagonal();
        this._setGraphContent();
        this._setRoot(data);

        return tree;
    }

    /**
    Getter for the cahced value of the data that initializes the graph.
    @method getData
    @return data object
    **/
    getData () {
        if (this._graphData) {
            return this._graphData;
        }
    }

    /**
    Sets the cached value of the svg diagonal object.
    @method _setDiagonal
    @private
    **/
    _setDiagonal () {
        this._diagonal = d3.svg.diagonal().projection((d) => {
            return [d.y, d.x];
        });
    }

    /**
    Getter for the diagonal object (used for node path creation).
    @method getDiagonal
    @return diagonal object
    **/
    getDiagonal () {
        if (this._diagonal) {
            return this._diagonal;
        }
    }

    /**
    Getter for the tooltip element
    @method getToolTip
    @return tooltip element
    **/
    getToolTip () {
        if (this._toolTip) {
            return this._toolTip;
        }
    }

    /**
    Creates the svg element and does initial translation before cacheing.
    @method _setGraphContent
    @private
    **/
    _setGraphContent () {
        const bb = this._boundingBox;
        const height = bb.offsetHeight;
        const width = bb.offsetWidth;

        let svg = d3.select(bb).append("svg")
                    .attr("width", width)
                    .attr("height", height)
                    .append("g")
                    .attr("transform", "translate(50,0)");

        this._setSVG(svg);
    }

    /**
    Sets the cached value of the svg element
    @method _setSVG
    @param {Node} svg
    @private
    **/
    _setSVG (svg) {
        this._svg = svg;
    }

    /**
    Getter for the cached value of the svg element.
    @method getSVG
    @return svg element
    **/
    getSVG () {
        if (this._svg) {
            return this._svg;
        }
    }

    /**
    Setter used for cacheing the value of the tree root.
    @method _setRoot
    @param {Object} data
    @private
    **/
    _setRoot (data) {
        const bb = this._boundingBox;
        const height = bb.offsetHeight;

        this._root = data[0];
        this._root.x0 = height / 2;
        this._root.y0 = 0;
    }

    /**
    Returns the cached value for the root of the tree
    @method getRoot
    @return root
    **/
    getRoot () {
        if (this._root) {
            return this._root;
        }
    }

    /**
    Updates the tree display (used for collapse/expand of branches).
    @method _updateTree
    @param {Object} source node
    @private
    **/
    _updateTree (source) {
        const tree = this._tree;
        const root = this.getRoot();

        // Compute the new tree layout.
        let treeNodes = tree.nodes(root).reverse(),
            links = tree.links(treeNodes),
            duration = 200;

        this._normalizeBranchSpacing(treeNodes);
        this._callToolTip();

        const nodes = this._getBranchNodes(treeNodes);

        this._enterNewNodes(source, nodes);
        this._transitionExitNodes(source, nodes, duration);
        this._transitionNodes(nodes, duration);
        this._updateLinkPaths(links, source, duration);
    }

    /**
    Sets up all the branch nodes
    @method _getBranchNodes
    @param {Object} treeNodes
    @return nodes
    @private
    **/
    _getBranchNodes (treeNodes) {
        const svg = this.getSVG();
        // Update the nodes…
        let i = 0;
        let nodes = svg.selectAll("g.node").data(treeNodes, (d) => {
            return d.id || (d.id = ++i);
        });

        return nodes
    }

    /**
    Normalizes the space between nodes on the branch
    @method _normalizeBranchSpacing
    @param {Object} treeNodes
    @private
    **/
    _normalizeBranchSpacing (treeNodes) {
        const bb = this._boundingBox;
        let maxDepth = 0;
        treeNodes.forEach((d) => {
            if (maxDepth < d.depth) {
                maxDepth = d.depth;
            }
        });
        const nodeSpace = bb.offsetWidth / (maxDepth + 1);
        treeNodes.forEach((d) => {
            d.y = d.depth * nodeSpace;
        });
    }

    /**
    Enter any new nodes at the parent's previous position.

    TODO: According to d3 docs, event handles should be removed before any are attached

    (https://github.com/d3/d3-selection/blob/master/README.md#handling-events).
    However, I am seeing event handles are increasing. Maybe because nodes
    aren't actually being destroyed? I find the implementation less than satisfying.
    **/
    _enterNewNodes (source, nodes) {
        const toolTip = this.getToolTip();
        let nodeEnter = nodes.enter().append("g")
                        .attr("class", "node")
                        .attr("transform", (d) => {
                            return "translate(" + source.y + "," + source.x + ")";
                        })
                        .on("click", this._onNodeClick.bind(this));

        nodeEnter.append("circle")
            .attr("r", 8)
            .attr("class", (d) => {
                let nodeClass = '';

                if (d.event.tags && d.event.tags.status) {
                    const status = d.event.tags.status[d.event.tags.status.length - 1];
                    if (status == 'fail') {
                        nodeClass = 'fail-event';
                    }
                } else if (d._children) {
                    nodeClass = 'collapsed';
                }

                return nodeClass;
            })
            .on('mouseover', this._showToolTip.bind(this))
            .on('mouseout', this._hideToolTip.bind(this));

        nodeEnter.append("text")
            .attr("dy", "3em")
            .attr("text-anchor", "middle")
            .text((d) => {
                return d["event"]["tags"]["source"][0];
            })
            .style("fill-opacity", 1);

        nodeEnter.append("text")
            .attr("dy", "4.3em")
            .attr("text-anchor", "middle")
            .text((d) => {
                let text = '';

                if (d["event"]["tags"]["type"][0] !== d["event"]["tags"]["source"][0]) {
                    text = d["event"]["tags"]["type"][0];
                }

                return text;
            })
            .style("fill-opacity", 1);
    }

    // Transition exiting nodes to the parent's new position.
    _transitionExitNodes (source, nodes, transitionSpeed) {
        let nodeExit = nodes.exit()
                            .transition()
                            .duration(transitionSpeed)
                            .attr("transform", (d) => {
                                return "translate(" + source.y + "," + source.x + ")";
                            })
                            .remove();

        nodeExit.select("circle")
                .attr("r", 0);

        nodeExit.select("text")
                .style("fill-opacity", 0);
    }

    // Transition nodes to their new position.
    _transitionNodes (nodes, transitionSpeed) {
        let nodeUpdate = nodes.transition()
                            .duration(transitionSpeed)
                            .attr("transform", (d) => {
                                return "translate(" + d.y + "," + d.x + ")";
                            });

        nodeUpdate.select("circle")
            .attr("class", (d) => {
                let className = '';

                if (d.event.tags && d.event.tags.status && d.event.tags.status[0] === 'fail') {
                    className = 'fail-event';
                } else if (d._children) {
                    className = 'collapsed';
                }

                return className;
            });

        nodeUpdate.select("text").style("fill-opacity", 1);
    }

    /**
    Update the paths between the nodes.
    @method _updateLinkPaths
    @param {Object} links - the node connections
    @param {Object} source - the node being operated on
    @param {Number} transitionSpeed - the number of ms in which to animate
    @private
    **/
    _updateLinkPaths (links, source, transitionSpeed) {
        const svg = this.getSVG();
        const diagonal = this.getDiagonal();

        let link = svg.selectAll("path.link")
                        .data(links, (d) => {
                            return d.target.id;
                        });

        // Enter any new links at the parent's previous position.
        link.enter()
            .insert("path", "g")
            .attr("class", "link")
            .attr("d", (d) => {
                let o = {x: source.x, y: source.y};
                return diagonal({source: o, target: o});
            });

        // Transition links to their new position.
        link.transition()
            .duration(transitionSpeed)
            .attr("d", diagonal);

        // Transition exiting nodes to the parent's new position.
        link.exit()
            .transition()
            .duration(transitionSpeed)
            .attr("d", (d) => {
                let o = {x: source.x, y: source.y};
                return diagonal({source: o, target: o});
            })
            .remove();
    }

    /**
    Toggle display of children on click.
    @method _onNodeClick
    @param {Node} node
    @private
    **/
    _onNodeClick (node) {
        if (node.children) {
            node._children = node.children;
            node.children = null;
        } else {
            node.children = node._children;
            node._children = null;
        }

        this._updateTree(node);
    }

    /**
    Creates the tooltip for use with node hover.
    @method _createToolTip
    @return d3-tip object
    @private
    **/
    _createToolTip () {
        const tip = d3.tip().attr('id', 'ets-tip')
                    .html((d) => { return this._getTipContent(d); })
                    .direction((d) => { return this._setTipDirection(d); });


        return tip;
    }

    /**
    Tells the graph to call the tooltip that was created.
    @method _callToolTip
    @private
    **/
    _callToolTip () {
        const toolTip = this.getToolTip();
        const svg = this.getSVG();

        if (toolTip) {
            svg.call(toolTip);

            const toolTipNode = document.getElementById('ets-tip');

            if (toolTipNode) {
                toolTipNode.onmouseover = () => { this._shortCircuitHide(); };
                toolTipNode.onmouseout = () => { this._hideToolTip(); };
            }
        }
    }

    /**
    Returns the tooltip content, based on the node event.

    TODO: This is better, but still needs some refactoring so we can test.

    @method _getTipContent
    @param {Node} d
    @return eventInfo
    @private
    **/
    _getTipContent (e) {
        if (!e) {
            return;
        }
        const eventData = e['event'];
        let eventInfo = '<dl>';

        let format = (term, desc) => {
            let t = '<dt>' + term.replace('_', ' ') + ':</dt>';
            let d = '<dd>' + desc + '</dd>';
            let item = t + d;
            return item;
        }

        let checkUrl = (itemString) => {
            let result = itemString;

            if (itemString.indexOf('@') !== -1) {
                result = `<a href="mailto:${itemString}">${itemString}</a>`;
            } else if (itemString.indexOf('http') !== -1) {
                result = `<a href="${itemString}">${itemString}</a>`;
            }

            return result;
        }

        let iterateArray = (obj, key) => {
            let arr = obj[key];
            let values = ''

            for(let j = 0; j < arr.length; j++) {
                if (j !== 0) {
                    values += ', ';
                }
                values += checkUrl(arr[j]);
            }

            return format(key, values);
        }

        let unpack = (obj) => {
            for (let key in obj) {
                if (typeof obj[key] === "object" && obj[key] !== null) {
                    if (Array.isArray(obj[key]) || typeof obj[key].length !== 'undefined') {
                        eventInfo += iterateArray(obj, key);
                    } else {
                        unpack(obj[key]);
                    }
                } else {
                    eventInfo += format(key, checkUrl(obj[key]));
                }
            }
        }

        // unpack the event object for all of its nested values
        unpack(eventData);

        eventInfo += '</dl>';

        return eventInfo;
    }

    /**
    Sets which direction to display a tooltip so it doesn't run outside the bounding box.

    TODO: d3-tip doesn't provide a good way to get the tip bounding box. Kind of fudging it here.

    @method _setTipDirection
    @param {d} node
    @return d3-tip direction
    @private
    **/
    _setTipDirection (d) {
        // we translate the axis of the graph, so here x & y are reflected on the line y=x
        const tipContent = document.getElementById('ets-tip');
        const rect = this._boundingBox.getBoundingClientRect();
        const fitsTop = d.x - rect.top > tipContent.offsetHeight;
        const tipHalfWidth = tipContent.offsetWidth / 2;
        const fitsLeft = d.y - rect.left > tipHalfWidth;
        const fitsRight = rect.right - d.y > tipHalfWidth;
        const fitsBottom = d.x - rect.bottom > tipContent.offsetHeight;

        let dir = 'n';

        if (!fitsTop && fitsLeft && fitsRight) {
            dir = 's';
        } else if (!fitsLeft && (fitsTop || fitsBottom)) {
            dir = 'e';
        } else if (!fitsRight && (fitsTop || fitsBottom)) {
            dir = 'w';
        } else if (!fitsTop && !fitsLeft) {
            dir = 'se';
        } else if (!fitsTop && !fitsRight) {
            dir = 'sw';
        }

        tipContent.className = dir;

        return dir;
    }

    /**
    Sets a timeout for calling the d3-tip hide method. This enables
    us a short window to move the mouse hover control to the tip
    itself before it disappears.
    @method _hideToolTip
    @param {e} d3 event
    @private
    **/
    _hideToolTip (e) {
        const toolTip = this.getToolTip();
        this._toolTipTimer = setTimeout(toolTip.hide, 150);
    }

    /**
    Provides a way to clear the tooltip hide timeout so we can
    transfer control to a tip hover.
    @method _shortCircuitHide
    @private
    **/
    _shortCircuitHide () {
        if (this._toolTipTimer) {
            clearTimeout(this._toolTipTimer);
            this._toolTipTimer = null;
        }
    }

    /**
    Allows us to call the timeout clear method before opening
    a new d3-tip. This is essential to ensure that there isn't
    an artificial close called on the tip.
    @method _showToolTip
    @param {e} d3 event
    @private
    **/
    _showToolTip (e) {
        const toolTip = this.getToolTip();
        this._shortCircuitHide();
        toolTip.show(e);
    }
}

module.exports = EtsGraph;
