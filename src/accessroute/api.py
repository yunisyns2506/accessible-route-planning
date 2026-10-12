from .algorithms import AccessibilityGraph

def create_sample_indoor_graph() -> AccessibilityGraph:
    """
    Test ve simülasyon amacıyla örnek bir kat planı grafı oluşturur:
    - corridor_1 (Ana koridor)
    - room_1 (Geniş kapı - 95 cm - Erişilebilir)
    - room_2 (Dar kapı - 75 cm - Erişilemez)
    - ramp_exit (Rampa çıkışı - %5 eğim - Erişilebilir)
    - stairs_exit (Merdiven çıkışı - Merdiven - Erişilemez)
    """
    g = AccessibilityGraph(min_width_cm=90.0, max_slope_deg=4.5)
    
    # Düğümler (x, y, z metre cinsinden)
    g.add_node("entrance", 0.0, 0.0, 0.0)
    g.add_node("corridor_1", 5.0, 0.0, 0.0)
    g.add_node("corridor_2", 10.0, 0.0, 0.0)
    g.add_node("room_1", 5.0, 3.0, 0.0)
    g.add_node("room_2", 10.0, 3.0, 0.0)
    g.add_node("ramp_exit", 15.0, 0.0, 0.5)

    # Kenarlar ve genişlikler (cm)
    g.add_edge("entrance", "corridor_1", width_cm=180.0)
    g.add_edge("corridor_1", "corridor_2", width_cm=180.0)
    g.add_edge("corridor_1", "room_1", width_cm=95.0)   # Erişilebilir kapı
    g.add_edge("corridor_2", "room_2", width_cm=75.0)   # Dar kapı (elenir)
    g.add_edge("corridor_2", "ramp_exit", width_cm=120.0, slope_deg=3.5) # Erişilebilir rampa

    return g

if __name__ == "__main__":
    g = create_sample_indoor_graph()
    res = g.find_accessible_route("entrance", "room_1")
    print("Oda 1 Rotası (Geniş kapı):", res)

    res_dar = g.find_accessible_route("entrance", "room_2")
    print("Oda 2 Rotası (Dar kapı):", res_dar)
