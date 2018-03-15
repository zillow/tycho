"use strict";
const expect = require('expect');
const jsdom = require('mocha-jsdom');
const sinon = require('sinon');
const EtsGraph = require('../EtsGraph');
const d3 = require('d3');
const d3tip = require('d3-tip')(d3);


jsdom();
// let window = document.defaultView;

let instance,
    boundingBox,
    tooltip,
    dataJSON;

describe('EtsGraph', () => {
    before(() => {
        dataJSON = [{"event":{"id":"222f1f77bcf86cd799439011","end_time":"2016-07-19T19:01:35.881000Z","tags":{"author":["mayurm@zillow.com"],"platform":["feature_zon_candidate"],"type":["commit"],"bug_number":["VEL-1306"],"concrete_commit":["222f1f77bcf86cd799439011"],"services":["egg.zonlib"],"source":["concrete"],"status":["success"]},"detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"start_time":"2016-07-19T19:00:35.881000Z","description":"This is a concrete event."},"children":[{"event":{"id":"578523547e7ac0645a2a661b","description":"This is a dms event.","tags":{"author":["mayurm@zillow.com"],"platform":["feature_zon_candidate"],"type":["auto-redeploy"],"services":["zon-web","tornado.zon-test-runner"],"source":["dms"],"status":["success"]},"parent_id":"222f1f77bcf86cd799439011","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:01:35.881000Z","end_time":"2016-07-19T19:02:45.881000Z"},"children":[{"event":{"id":"5785240d7e7ac0645a2a661c","description":"This is a concrete event.","tags":{"author":["mayurm@zillow.com"],"platform":["feature_zon_candidate"],"type":["commit"],"bug_number":["VEL-1306"],"concrete_commit":["5785240d7e7ac0645a2a661c"],"services":["tornado.zon-test-runner"],"source":["concrete"],"status":["success"]},"parent_id":"578523547e7ac0645a2a661b","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:02:55.881000Z","end_time":"2016-07-19T19:03:30.881000Z"},"children":[{"event":{"id":"111f1f77bcf86cd799439011","description":"This is a trigger_deploy event.","tags":{"author":["mayurm@zillow.com"],"type":["trigger-deploy"],"environment":["monitor_candidate"],"services":["tornado.zon-test-runner"],"source":["trigger-deploy"],"status":["success"]},"parent_id":"5785240d7e7ac0645a2a661c","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:03:55.881000Z","end_time":"2016-07-19T19:04:35.881000Z"},"children":[{"event":{"id":"5498d53c5f2d60095267a0bb","description":"This is a mozart event.","tags":{"author":["mayurm@zillow.com"],"type":["deploy/deploy_all"],"environment":["monitor_candidate"],"services":["tornado.zon-test-runner"],"source":["mozart"],"status":["success"]},"parent_id":"111f1f77bcf86cd799439011","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:05:35.881000Z","end_time":"2016-07-19T19:06:35.881000Z"},"children":[{"event":{"id":"333f1f77bcf86cd799439333","description":"This is a deploy tools event.","tags":{"author":["mayurm@zillow.com"],"type":["full-deploy/start"],"environment":["monitor_candidate"],"services":["tornado.zon-test-runner"],"source":["deploy-tools"],"status":["success"]},"parent_id":"5498d53c5f2d60095267a0bb","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:07:35.881000Z","end_time":"2016-07-19T19:08:35.881000Z"},"children":[]}]}]}]},{"event":{"id":"57852376e407e125d0d9f54c","description":"This is a concrete event.","tags":{"author":["mayurm@zillow.com"],"platform":["feature_zon_candidate"],"type":["commit"],"bug_number":["VEL-1306"],"concrete_commit":["57852376e407e125d0d9f54c"],"services":["zon-web"],"source":["concrete"],"status":["fail"]},"parent_id":"578523547e7ac0645a2a661b","detail_urls":{"zbrt":"https://zbrt.atl.zillow.net/browse/VEL-1306"},"source_id":"222f1f77bcf86cd799439011","start_time":"2016-07-19T19:02:55.881000Z","end_time":"2016-07-19T19:03:35.881000Z"},"children":[]}]}]}];

        boundingBox = document.createElement('div');
        boundingBox.setAttribute('id', 'graph');
        boundingBox.setAttribute('style', 'height:600px;margin:0 5%;width:1000px;box-sizing:border-box;top:0;');
        // jsdom does not actually render the dom, so offsetHeight and offsetWidth are not calculated.
        // d3 relies on these attributes during svg render, so setting it here explicitly.
        boundingBox.offsetHeight = '600';
        boundingBox.offsetWidth = '1000';
        document.body.appendChild(boundingBox);

        tooltip = document.createElement('div');
        tooltip.setAttribute('id', 'ets-tip');
        tooltip.offsetHeight = '300';
        tooltip.offsetWidth = '400';
        document.body.appendChild(tooltip);

        instance = new EtsGraph(dataJSON, 'graph');
    });

    after(() => {
        boundingBox.remove();
        boundingBox = null;
        instance = null;
    });

    it('should cache the graph data', () => {
        const data = instance.getData();

        expect(data).toNotBe(null);
        expect(Array.isArray(data)).toBe(true);
        expect(data.length).toBe(1);
        expect(typeof data[0].event).toBe('object');
    });

    it('should cache the parent container', () => {
        const bb = instance._boundingBox;

        expect(bb).toNotBe(null);
        expect(bb.getAttribute('id')).toBe('graph');
        expect(bb.style.width).toBe('1000px');
    });

    describe('d3 tree creation', () => {
        it('should create a tree object', () => {
            const data = instance.getData();
            const tree = instance._createTree(data);

            expect(tree).toNotBe(null);
            expect(typeof tree).toBe('function');
            expect(tree.size().length).toBe(2);
            expect(tree.size()[0]).toBe('600');
            expect(tree.size()[1]).toBe('1000');
        });

        describe('creating graph elements', () => {
            it('should save the created tree object parts for reuse', () => {
                let diagonalSpy = sinon.spy(instance, '_setDiagonal');
                let graphContentSpy = sinon.spy(instance, '_setGraphContent');
                let rootSpy = sinon.spy(instance, '_setRoot');
                const data = instance.getData();
                const tree = instance._createTree(data);

                expect(diagonalSpy.calledOnce).toBe(true);
                expect(diagonalSpy.calledTwice).toBe(false);
                expect(graphContentSpy.calledOnce).toBe(true);
                expect(graphContentSpy.calledTwice).toBe(false);
                expect(rootSpy.calledOnce).toBe(true);
                expect(rootSpy.calledTwice).toBe(false);

                // restore the spies
                diagonalSpy.restore();
                graphContentSpy.restore();
                rootSpy.restore();
            });

            it('should create the path between nodes', () => {
                const data = instance.getData();
                const tree = instance._createTree(data);
                let diagonal = instance.getDiagonal();
                expect(typeof diagonal).toBe('function');
            });

            it('should create the main svg element', () => {
                const data = instance.getData();
                const tree = instance._createTree(data);
                let svg = instance.getSVG();
                expect(typeof svg).toBe('object');
            });

            it('should create the root element of the graph', () => {
                const data = instance.getData();
                const tree = instance._createTree(data);
                let root = instance.getRoot();
                expect(typeof root).toBe('object');
                expect(root).toEqual(dataJSON[0]);
                expect(root.children.length).toEqual(1);
            });
        });

        it('should update the tree', () => {
            // d3 tooltip is a PITA - ignore it for this test
            sinon.stub(instance, "_callToolTip", () => { return false; });
            instance.render();

            let enterSpy = sinon.spy(instance, '_enterNewNodes');
            let transitExitSpy = sinon.spy(instance, '_transitionExitNodes');
            let transitSpy = sinon.spy(instance, '_transitionNodes');
            let linkUpdateSpy = sinon.spy(instance, '_updateLinkPaths');
            let normalizeSpy = sinon.spy(instance, '_normalizeBranchSpacing');

            instance._updateTree(root);

            expect(enterSpy.calledOnce).toBe(true);
            expect(transitExitSpy.calledOnce).toBe(true);
            expect(transitSpy.calledOnce).toBe(true);
            expect(linkUpdateSpy.calledOnce).toBe(true);
            expect(normalizeSpy.calledOnce).toBe(true);

            // restore the spies
            enterSpy.restore();
            transitExitSpy.restore();
            transitSpy.restore();
            linkUpdateSpy.restore();
            normalizeSpy.restore();
        });

        it('should return branch nodes', () => {
            let root = instance.getRoot();
            const data = instance.getData();
            const tree = instance._tree;
            const treeNodes = tree.nodes(root).reverse();
            const nodes = instance._getBranchNodes(treeNodes);

            expect(typeof nodes).toBe('object');
            expect(nodes.length).toBe(1);
            expect(nodes[0].length).toBe(7);
            expect(typeof nodes.enter).toBe('function');
            expect(typeof nodes.exit).toBe('function');
        });
    });

    describe('nodes spacing', () => {
        it('should be spaced based on node depth', () => {
            const data = instance.getData();
            const tree = instance._tree = instance._createTree(data);
            let treeNodes = tree.nodes(instance.getRoot()).reverse();
            instance._normalizeBranchSpacing(treeNodes);

            let maxDepth = 0;
            treeNodes.forEach((d) => {
                if (maxDepth < d.depth) {
                    maxDepth = d.depth;
                }
            });

            const nodeSpace = tree.size()[1] / (maxDepth + 1);
            treeNodes.forEach((n) => {
                expect(n.y).toBe(n.depth * nodeSpace);
            });
        });
    }),

    describe('node interactions', () => {
        it('should update the tree when a node is clicked', () => {
            let root = instance.getRoot();
            const data = instance.getData();
            const tree = instance._tree;
            const treeNodes = tree.nodes(root).reverse();

            let updateSpy = sinon.spy(instance, '_updateTree');

            let activeNode = treeNodes[3];
            instance._onNodeClick(activeNode);
            expect(updateSpy.calledOnce).toBe(true);
            expect(updateSpy.calledWith(activeNode)).toBe(true);

            updateSpy.restore();
        });

        it('should show the tooltip', () => {
            const data = instance.getData();
            const event = data[0];
            const tooltip = instance.getToolTip();

            let shortCircuitSpy = sinon.spy(instance, '_shortCircuitHide');
            // jsdom doesn't support SVGElement, which d3-tip checks against, so must stub around it
            let tooltipShowStub = sinon.stub(tooltip, "show", () => { return true; });

            instance._showToolTip(event);

            expect(shortCircuitSpy.calledOnce).toBe(true);
            expect(tooltipShowStub.calledOnce).toBe(true);

            shortCircuitSpy.restore();
        });

        it('should hide the tooltip', () => {
            const data = instance.getData();
            const event = data[0];
            const tooltip = instance.getToolTip();
            const svg = instance.getSVG();

            expect(instance._toolTipTimer).toBe(undefined);
            instance._hideToolTip(event);
            expect(instance._toolTipTimer).toNotBe(undefined);
            expect(typeof instance._toolTipTimer).toBe('object');
            expect(instance._toolTipTimer._idleTimeout).toBe(150);

        });

        it('should be able to short circuit the tooltip hide timer', () => {
            const data = instance.getData();
            const event = data[0];
            const tooltip = instance.getToolTip();
            const svg = instance.getSVG();

            instance._hideToolTip(event);
            expect(instance._toolTipTimer).toNotBe(undefined);
            instance._shortCircuitHide();
            expect(instance._toolTipTimer).toBe(null);
        });

        it('should set the direction of the tooltip display', () => {
            // we are limited in this test because jsdom can't support getBoundingClientRect,
            // because no layout... so height is 0
            let dir = instance._setTipDirection({x: 500, y: 400});
            expect(dir).toBe('w');

            dir = instance._setTipDirection({x: -1000, y: -500});
            expect(dir).toBe('se');

            dir = instance._setTipDirection({x: 500, y: -200});
            expect(dir).toBe('e');

            dir = instance._setTipDirection({x: -10000, y: 10000});
            expect(dir).toBe('sw');
        });

        it('should get tip content for display', () => {
            const data = instance.getData();
            const event = data[0];
            let tipContent = instance._getTipContent(event);
            expect(tipContent).toNotBe(null);
            expect(tipContent).toBe('<dl><dt>id:</dt><dd>222f1f77bcf86cd799439011</dd><dt>end time:</dt><dd>2016-07-19T19:01:35.881000Z</dd><dt>author:</dt><dd><a href="mailto:mayurm@zillow.com">mayurm@zillow.com</a></dd><dt>platform:</dt><dd>feature_zon_candidate</dd><dt>type:</dt><dd>commit</dd><dt>bug number:</dt><dd>VEL-1306</dd><dt>concrete commit:</dt><dd>222f1f77bcf86cd799439011</dd><dt>services:</dt><dd>egg.zonlib</dd><dt>source:</dt><dd>concrete</dd><dt>status:</dt><dd>success</dd><dt>zbrt:</dt><dd><a href="https://zbrt.atl.zillow.net/browse/VEL-1306">https://zbrt.atl.zillow.net/browse/VEL-1306</a></dd><dt>start time:</dt><dd>2016-07-19T19:00:35.881000Z</dd><dt>description:</dt><dd>This is a concrete event.</dd></dl>');
        });
    });
});
