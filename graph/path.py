# Find some paths between two nodes.
# It will take too long to order all the paths through the graph,
# so we will find heuristicly good paths.

import queue
import sys

# import loadGraph

DEFAULT_NUM_PATHS = 5

# After we find the required number of paths, search for this additional number of iterations.
ADDITIONAL_SEARCH_TIME = 3

# Return [(neighbor, edge cost, inner edge?)]
def getNeighbors(graph, id):
    neighbors = []

    for neighborId in graph[id]:
        neighbors.append((neighborId, graph[id][neighborId][0], graph[id][neighborId][1]))

    return neighbors

# The base cost is the cost of the path up until this point.
def enqueueNeighbors(targetQueue, graph, seenNodes, paths, id, endId):
    neighbors = getNeighbors(graph, id)
    baseCost = seenNodes[id][0]

    for (neighbor, cost, isInner) in neighbors:
        totalCost = baseCost + cost

        # If we found a path.
        if (neighbor == endId):
            newPath = list(seenNodes[id][1])
            newPath.append(neighbor)
            paths.append((totalCost, newPath))

            continue

        # If the neighbor is a non-person (the edge is an outer edge),
        # then skip this neighbor.
        # Note that we already checked for the target.
        if (not isInner):
            continue

        if (neighbor in seenNodes):
            # If the current path has a shorter cost than the already seen one,
            # then replace it.
            if (totalCost < seenNodes[neighbor][0]):
                # Copy the existing path to id, then add the neighbor.
                newPath = list(seenNodes[id][1])
                newPath.append(neighbor)
                seenNodes[neighbor] = (totalCost, newPath)
        else:
            targetQueue.put((totalCost, neighbor))

            newPath = list(seenNodes[id][1])
            newPath.append(neighbor)
            seenNodes[neighbor] = (totalCost, newPath)

# Note that we expect to start from a person and end at a non-person.
# So we will ensure that all of our edges (except for the last one) are inner edges.
# Return [[path], ...]
def findRawPaths(startId, endId, numPaths, graph = None):
    if (startId == endId or startId not in graph or endId not in graph):
        return []

    if (graph == None):
        graph = loadGraph.fetchGraph()

    paths = []

    # Keep track of every node we have seen, the cost to get to that node, and the path.
    # {node: (cost, [node, p, a, t, h, ...]), ...}.
    # If we get a better path to the same node, then we will replace it.
    # Start with the starting node.
    seenNodes = {
        startId: (0.0, [startId])
    }

    # The edges to explore.
    # Explore the lowest cost paths first.
    # [(cost, (from, to)), ...]
    toExplore = queue.PriorityQueue()

    # We will search a few iterations after we find enough paths.
    additionalSearchTime = 0

    # Start by exporing the neighbors.
    enqueueNeighbors(toExplore, graph, seenNodes, paths, startId, endId)

    while (not toExplore.empty() and additionalSearchTime < ADDITIONAL_SEARCH_TIME):
        score, toNode = toExplore.get()

        # If we didn't reach the target, then enqueue all the neighbors and try again.
        enqueueNeighbors(toExplore, graph, seenNodes, paths, toNode, endId)

        if (len(paths) >= numPaths):
            additionalSearchTime += 1

    return sorted(paths)[:numPaths]

# findRawPaths(), but with additional information about the edges and nodes.
# (paths, edge indormation, node information)
# ([[path], ...], {fromId: {toId: cost, ...}, ...}, {entityId: (facebook id, name, isPerson)})
def findPaths(startId, endId, numPaths, graph = None, entities = None):
    if (graph == None):
        graph = loadGraph.fetchGraph()

    if (entities == None):
        entities = loadGraph.fetchEntities()

    # Paths
    paths = [path[1] for path in findRawPaths(startId, endId, numPaths, graph)]

    # Edges
    edgeInfo = {}
    for path in paths:
        for i in range(len(path) - 1):
            edgeStart = path[i]
            edgeEnd = path[i + 1]
            edgeCost = graph[edgeStart][edgeEnd][0]

            if (edgeStart not in edgeInfo):
                edgeInfo[edgeStart] = {}

            edgeInfo[edgeStart][edgeEnd] = edgeCost

    # Nodes
    nodes = {}
    for path in paths:
        for node in path:
            nodes[node] = entities[node]

    return paths, edgeInfo, nodes

def parseArgs(scriptName, args):
    if (len(args) < 2 or len(args) > 3 or 'help' in [arg.lower().strip().replace('-', '') for arg in args]):
        print("USAGE: python3 %s <source id> <target id> [num paths]" % (scriptName))
        sys.exit(1)

    startId = int(args.pop(0))
    endId = int(args.pop(0))

    numPaths = DEFAULT_NUM_PATHS
    if (len(args) > 0):
        numPaths = int(args.pop(0))

    return startId, endId, numPaths

def main():
    startId, endId, numPaths = parseArgs(sys.argv[0], sys.argv[1:])

    paths, edgeInfo, nodes = findPaths(startId, endId, numPaths)

    for path in paths:
        pathOutput = []
        cost = 0.0

        for i in range(len(path) - 1):
            edgeCost = edgeInfo[path[i]][path[i + 1]]
            pathOutput.append(nodes[path[i]][1])
            pathOutput.append("(%f)" % (edgeCost))
            cost += edgeCost

        pathOutput.append(nodes[path[-1]][1])
        pathOutput.insert(0, str(cost))

        print(' '.join(pathOutput))

if __name__ == '__main__':
    main()
