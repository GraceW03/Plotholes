from backend.models.BlockedEdges import BlockedEdges
from backend.app import create_app
import osmnx as ox
import networkx as nx
import matplotlib as plot
import os

def get_shortest_path(graph, orig_node, dest_node, blocked_edges_set):
    """
    Compute the shortest path on a given OSMnx graph, avoiding blocked edges.

    graph: OSMnx graph
    origin_point: nearest node to origin lat/lon
    destination_point: nearest node to destination lat/lon
    blocked_edges_set: cached set of blocked edges from database

    Returns: path (list of node IDs)
    """
    # --- 1) Define a custom weight function that avoids blocked edges ---
    def weight(u, v, data):
        if (u, v, 0) in blocked_edges_set:
            return float('inf')  # hard block
        # Use travel_time if available, else fallback to length
        return data.get('travel_time', data.get('length', 1))

    # --- 2) Compute shortest path ---
    try:
        path = nx.shortest_path(graph, source=orig_node, target=dest_node, weight=weight)
        return path
    except nx.NetworkXNoPath:
        print("No available path avoiding blocked edges.")
        return None
    
def get_subgraph(graph, origin_point, destination_point, margin=0.02):
    """
    Returns a subgraph containing nodes near the origin and destination.

    graph: full OSMnx graph
    origin_point: (lat, lon)
    destination_point: (lat, lon)
    margin: extra padding in degrees (~0.01 ≈ 1 km)

    Returns: subgraph (NetworkX MultiDiGraph)
    """
    # Determine bounding box
    min_lat = min(origin_point[0], destination_point[0]) - margin
    max_lat = max(origin_point[0], destination_point[0]) + margin
    min_lon = min(origin_point[1], destination_point[1]) - margin
    max_lon = max(origin_point[1], destination_point[1]) + margin

    # Get nodes within bounding box
    nodes = [
        n for n, d in graph.nodes(data=True)
        if min_lat <= d['y'] <= max_lat and min_lon <= d['x'] <= max_lon
    ]

    # Return subgraph
    return graph.subgraph(nodes).copy()

def convert_latlon_to_node(graph, point):
    """
    Converts the point to a node

    graph: OSMnx graph
    point: tuple (lat, lon)

    Returns: node
    """
    return ox.distance.nearest_nodes(graph, X=point[1], Y=point[0])

def visualize_large(graph, route):
    """
    Visualizes the route on the overall graph
    """
    if route:
            ox.plot_graph_route(nyc_graph, route)
    else:
        print("No route created")

def visualize_zoomed(graph, route, origin_node, destination_node):
    # Get node coordinates for the route
    route_xs = [graph.nodes[n]['x'] for n in route]
    route_ys = [graph.nodes[n]['y'] for n in route]
    margin = 0.001

    # Plot route
    fig, ax = ox.plot_graph_route(
        graph,
        route,
        route_color='red',
        route_linewidth=3,
        node_size=0,
        bgcolor='white',
        show=False,
        close=False
    )

    # Zoom to route
    ax.set_xlim(min(route_xs) - margin, max(route_xs) + margin)
    ax.set_ylim(min(route_ys) - margin, max(route_ys) + margin)

    # Plot origin and destination markers
    ax.scatter(graph.nodes[origin_node]['x'], nyc_graph.nodes[origin_node]['y'], c='green', s=100, zorder=5)
    ax.scatter(graph.nodes[destination_node]['x'], nyc_graph.nodes[destination_node]['y'], c='blue', s=100, zorder=5)

    plot.pyplot.show()

if __name__ == '__main__':
    # Initialize Flask app + DB context
    app = create_app()

    with app.app_context():
        # TODO: CACHE THIS - load blocked edges on startup of app
        blocked_edges_set = app.blocked_edges_set  # use cached set

        # Load in graph of map
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        GRAPH_PATH = os.path.join(BASE_DIR, 'data', 'nyc_graphml.graphml')
        nyc_graph = ox.load_graphml(GRAPH_PATH)

        # Define latitude and longitude of origin and destination
        origin = (40.681722, -73.832725)
        destination = (40.682725, -73.829194)

        # Find subgraph around origin/destination
        subgraph = get_subgraph(nyc_graph, origin, destination, margin=0.02)

        # Find the node on the graph closest to this longitude and latitudes
        origin_node = convert_latlon_to_node(subgraph, origin)
        dest_node = convert_latlon_to_node(subgraph, destination)

        # Get the shortest path that avoids blocked streets
        route = get_shortest_path(subgraph, orig_node=origin_node, dest_node=dest_node, blocked_edges_set=blocked_edges_set)

        # # Create large visualization
        # visualize_large(nyc_graph, route)

        # Create zoomed-in visualization
        visualize_zoomed(nyc_graph, route=route, origin_node=origin_node, destination_node=dest_node)


        #### SECOND ONE:
        # Define latitude and longitude of origin and destination
        origin = (40.672664, -73.970471)
        destination = (40.674402, -73.975413)

        # Find subgraph around origin/destination
        subgraph = get_subgraph(nyc_graph, origin, destination, margin=0.02)

        # Find the node on the graph closest to this longitude and latitudes
        origin_node = convert_latlon_to_node(subgraph, origin)
        dest_node = convert_latlon_to_node(subgraph, destination)

        # Get the shortest path that avoids blocked streets
        route = get_shortest_path(subgraph, orig_node=origin_node, dest_node=dest_node, blocked_edges_set=blocked_edges_set)

        # # Create large visualization
        # visualize_large(nyc_graph, route)

        # Create zoomed-in visualization
        visualize_zoomed(nyc_graph, route=route, origin_node=origin_node, destination_node=dest_node)




