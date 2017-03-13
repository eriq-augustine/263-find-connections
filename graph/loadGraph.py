# Handle loading the graph.
# The retuned graph will have edge costs instead of score.
# (So lower is better).

import os
import pickle

# Figure it out relative to this file.
PICKLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pickles')
GRAPH_PICKLE_FILE = os.path.join(PICKLE_DIR, 'graph.pickle')
ENTITIES_PICKLE_FILE = os.path.join(PICKLE_DIR, 'entities.pickle')

# This / edge score = edge cost.
NORMALIZER = 5.0

DB_HOST = 'localhost'
DB_NAME = 'facebook'

def fetchFromDB(query):
    # We will only import the database driver if we actually need it.
    # If we have the pickle, we can just load that instead.
    import psycopg2

    connectionString = "host='%s' dbname='%s'" % (DB_HOST, DB_NAME)
    conn = psycopg2.connect(connectionString)
    cur = conn.cursor()

    cur.execute(query)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

# Represent the graph as a map of maps.
# {fromId: {toId: (cost, isInner), ...}, ...}
# "Inner" edges are only between people.
# Note that the graph is undirected, but we must represent undirected edges as two entries for efficiency.
def fetchGraph():
    if (os.path.isfile(GRAPH_PICKLE_FILE)):
        return pickle.load(open(GRAPH_PICKLE_FILE, 'rb'))

    graph = fetchGraphFromDB()
    pickle.dump(graph, open(GRAPH_PICKLE_FILE, 'wb'))

    return graph

def fetchGraphFromDB():
    query = '''
        SELECT
            fromEntityId,
            toEntityId,
            score,
            isInner
        FROM Edges
    '''
    edges = fetchFromDB(query)

    graph = {}
    for edge in edges:
        if (edge[0] not in graph):
            graph[edge[0]] = {}

        graph[edge[0]][edge[1]] = (max(0.05, 1 - edge[2] / NORMALIZER), edge[3])

    return graph

# {id: (facebookId, name, isPerson, base64Image), ...}
def fetchEntities():
    if (os.path.isfile(ENTITIES_PICKLE_FILE)):
        return pickle.load(open(ENTITIES_PICKLE_FILE, 'rb'))

    entities = fetchEntitiesFromDB()
    pickle.dump(entities, open(ENTITIES_PICKLE_FILE, 'wb'))

    return entities

def fetchEntitiesFromDB():
    query = '''
        SELECT
            id,
            facebookId,
            name,
            isPerson,
            imageBase64
        FROM Entities
    '''
    rows = fetchFromDB(query)

    entities = {}
    for row in rows:
        entities[row[0]] = (row[1], row[2], row[3], row[4])

    return entities

# {facebookId: id, ...}
def fetchFacebookIdMap():
    entities = fetchEntities()

    idMap = {}
    for entityId in entities:
        idMap[entities[entityId][0]] = entityId

    return idMap

# {id: (facebookId, name, isPerson), ...}
def fetchBareEntities():
    entities = fetchEntities()

    bareEntities = {}
    for entityId in entities:
        bareEntities[entityId] = entities[entityId][:3]

    return bareEntities

def main():
    graph = fetchGraph()
    print("Num Edges: ", len(graph))

    entities = fetchEntities()
    print("Num Entities: ", len(entities))

    idMap = fetchFacebookIdMap()
    print("Num Id Map: ", len(idMap))

    # eriq.augustine - 10091
    print(graph[10091])
    print(entities[10091])
    print(idMap['eriq.augustine'])

if __name__ == '__main__':
    main()
