import math
import heapq
from typing import Dict, List, Tuple, Optional, Any

class AccessibilityGraph:
    """
    TS 9111 Engelli Erisilebilirlik Standartlarina uygun ic mekan topolojik grafi.
    Tekerlekli sandalye gecis genisligi (min 90 cm) ve egim kısıtlarini uygular.
    """
    def __init__(self, min_width_cm: float = 90.0, max_slope_deg: float = 4.5):
        self.min_width_cm = min_width_cm
        self.max_slope_deg = max_slope_deg
        self.nodes: Dict[str, Tuple[float, float, float]] = {}  # id -> (x, y, z)
        self.edges: Dict[str, List[Dict[str, Any]]] = {}  # id -> list of {target, width, slope, surface_cost}

    def add_node(self, node_id: str, x: float, y: float, z: float):
        self.nodes[node_id] = (x, y, z)
        if node_id not in self.edges:
            self.edges[node_id] = []

    def add_edge(self, u: str, v: str, width_cm: float, slope_deg: float = 0.0, surface_cost: float = 1.0, bidirectional: bool = True):
        edge_data_uv = {
            "target": v,
            "width_cm": width_cm,
            "slope_deg": slope_deg,
            "surface_cost": surface_cost
        }
        self.edges[u].append(edge_data_uv)

        if bidirectional:
            edge_data_vu = {
                "target": u,
                "width_cm": width_cm,
                "slope_deg": -slope_deg,
                "surface_cost": surface_cost
            }
            self.edges[v].append(edge_data_vu)

    def heuristic(self, u: str, v: str) -> float:
        """Oklid mesafesi sezgiseli (Euclidean Distance Heuristic)"""
        x1, y1, z1 = self.nodes[u]
        x2, y2, z2 = self.nodes[v]
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)

    def find_accessible_route(self, start: str, goal: str) -> Optional[Dict[str, Any]]:
        """
        A* Algoritmasi ile tekerlekli sandalye profiline uygun en kisa erisilebilir rotayi bulur.
        """
        if start not in self.nodes or goal not in self.nodes:
            return None

        open_set = []
        heapq.heappush(open_set, (0.0, start))
        
        came_from: Dict[str, str] = {}
        g_score: Dict[str, float] = {node: float("inf") for node in self.nodes}
        g_score[start] = 0.0

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                # Rotayi yeniden insa et
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return {
                    "path": path,
                    "total_cost": g_score[goal],
                    "accessible": True
                }

            x1, y1, z1 = self.nodes[current]

            for edge in self.edges.get(current, []):
                neighbor = edge["target"]
                width = edge["width_cm"]
                slope = edge["slope_deg"]

                # TS 9111 Erisilebilirlik Kısıt Kontrolu
                if width < self.min_width_cm or abs(slope) > self.max_slope_deg:
                    continue  # Bu gecit tekerlekli sandalye icin uygun degil

                x2, y2, z2 = self.nodes[neighbor]
                dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
                cost = dist * edge["surface_cost"] * (1.0 + max(0.0, slope) * 0.1)

                tentative_g = g_score[current] + cost
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None  # Uygun erisilebilir rota bulunamadi
