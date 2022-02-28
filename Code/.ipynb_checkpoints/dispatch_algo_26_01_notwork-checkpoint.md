 # add carrying orders (customer location) into all locations set
    #     if len(carrying_orders) > 0:
    #         pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders(carrying_orders, id_to_location)
    #         driver_id_to_planned_route[driver_id].extend(pickup_node_list)
    #         driver_id_to_planned_route[driver_id].extend(delivery_node_list)
        
    # # pre-matching orders
    # pre_matching_order_ids = []
    # for driver_id, driver in id_to_driver.items():
    #     if len(driver.carrying_orders) == 0 and driver.destination is not None:
    #         pickup_orders = driver.destination.pickup_orders
    #         pre_matching_order_ids.extend([order.id for order in pickup_orders])
    #         pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders(pickup_orders, id_to_location)
    #         driver_id_to_planned_route[driver_id].extend(pickup_node_list)
    #         driver_id_to_planned_route[driver_id].extend(delivery_node_list)
                
    #     if len(driver.carrying_orders) == 0 and driver.planned_route != []:
    #         for node in driver.planned_route:
    #             node_pickup_orders = node.pickup_orders
    #             node_delivery_orders = node.delivery_orders
    #             pre_matching_order_ids.extend([order.id for order in node_pickup_orders])
    #             pre_matching_order_ids.extend([order.id for order in node_delivery_orders])
    #             pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders(pickup_orders, id_to_location)
    #             driver_id_to_planned_route[driver_id].extend(pickup_node_list)
    #             driver_id_to_planned_route[driver_id].extend(delivery_node_list)
        
    
    # # unallocated orders
    # driver_id_to_left_capacity = __get_left_capacity_of_driver(id_to_driver)
    # for order_id, order in id_to_unallocated_order.items():
    #     available_driver_ids = [driver_id for driver_id, driver in id_to_driver.items() if driver_id_to_left_capacity[driver_id] > 0]
    #     if order_id in pre_matching_order_ids:
    #         continue
    #     # order pickup & delivery node object
    #     pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders([order], id_to_location)
    #     if pickup_node_list == [] or delivery_node_list == []:
    #         continue
    #     # assign order to driver will maximum available capacity
    #     assign_driver_id = max(driver_id_to_left_capacity, key=driver_id_to_left_capacity.get)
    #     assign_driver = id_to_driver.get(assign_driver_id)
    #     driver_id_to_planned_route[assign_driver.id].extend(pickup_node_list)
    #     driver_id_to_planned_route[assign_driver.id].extend(delivery_node_list)
    #     driver_id_to_left_capacity[assign_driver_id] -= 1
    
    
    # # re-optimized planned route by solving a VRP for each driver
    # for driver_id, driver in id_to_driver.items():
    #     driver_planned_route = driver_id_to_planned_route.get(driver_id)
    #     depot = driver_planned_route[0]
    #     visited_locations = [node.id for node in driver_planned_route] 
    #     # pickup delivery index pair 
    #     pairs = []
    #     i = 1
    #     while i < len(visited_locations):
    #         pairs.append([i, i+1])
    #         i += 2
    #     # remove duplicate locations
    #     visited_locations = list(dict.fromkeys(visited_locations)) 
    #     num_visited_locations = len(visited_locations)
    #     distance_matrix = np.zeros(shape=(num_visited_locations, num_visited_locations))
    #     for index_1, location_1_id in enumerate(visited_locations):
    #         for index_2, location_2_id in enumerate(visited_locations):
    #             location_1 = id_to_location.get(location_1_id)
    #             location_2 = id_to_location.get(location_2_id)
    #             distance_matrix[index_1, index_2] = hs.haversine((location_1.lat, location_1.lng), (location_2.lat, location_2.lng))
    #     print(pairs)
    #     print(distance_matrix)
    #     logger.info(f"start to plan the route for driver: {driver_id}")
    #     data = create_data_model(distance_matrix, pairs, 1, 0)
    #     output_route = run(data)
    #     if output_route != []:
    #         visite_sequence = output_route[0][:-1] # index of planned route
    #     else:
    #         visite_sequence = []
    #     new_planned_route = [driver_planned_route[i] for i in visite_sequence]
    #     driver_id_to_planned_route[driver_id] = new_planned_route
    #     logger.info(f"Finish the plan the route for driver: {driver_id}")