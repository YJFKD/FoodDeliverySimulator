import os
import copy
import numpy as np
import haversine as hs
from python_tsp.exact import solve_tsp_dynamic_programming


from src.common.node import Node
from src.common.route import Map
from src.configuration.config import Configs
from src.utils.input_utils import get_restaurant_info, get_customer_info
from src.utils.json_tools import convert_nodes_to_json, write_json_to_file_append
from src.utils.json_tools import get_driver_instance_dict, get_order_dict
from src.utils.json_tools import read_json_from_file, write_json_to_file
from src.utils.logging_engine import logger
from src.utils.or_tools import create_data_model, run


def dispatch_orders_to_drivers(id_to_unallocated_order: dict, id_to_driver: dict, id_to_location: dict):
    """
    Inputs:
    - id_to_unallocated_order: {order_id ——> Order object(state: "GENERATED")}
    - id_to_driver: {driver_id: driver object}
    - id_to_location: {location_id: location object (restaurant or customer)}
    """
    driver_id_to_destination = {}
    driver_id_to_planned_route = {} # planned route should include both pickup and delivery location

    # for non-empty driver, based on the carrying orders, generate planned_route
    for driver_id, driver in id_to_driver.items():
        driver_id_to_planned_route[driver_id] = []
        carrying_orders = driver.carrying_orders
        # initialize the location of driver
        if driver.current_location_id != "":
            driver_location_id = driver.current_location_id
            # driver_id_to_planned_route[driver_id] = [] 
        else:
            driver_location_id = driver.destination.id
            # location = driver.destination
            # node = Node(driver_location_id, location.lat, location.lng, location.pickup_orders, location.delivery_orders)
            # driver_id_to_planned_route[driver_id] = [node] # if driver has destination, add it into planned route
        
        all_locations_id = [driver_location_id]
        if len(carrying_orders) > 0:
            # driver & order location id
            for order in carrying_orders:
                customer_location_id = order.delivery_location_id
                all_locations_id.append(customer_location_id)
            num_locations = len(all_locations_id)
            
            # construct distance matrix
            distance_matrix = np.zeros(shape=(num_locations, num_locations))
            for index_1, location_1_id in enumerate(all_locations_id):
                for index_2, location_2_id in enumerate(all_locations_id):
                    location_1 = id_to_location.get(location_1_id)
                    location_2 = id_to_location.get(location_2_id)
                    distance_matrix[index_1, index_2] = hs.haversine((location_1.lat, location_1.lng), (location_2.lat, location_2.lng))
            
            # driver routing as a TSP
            visiting_sequence, travel_distance = solve_tsp_dynamic_programming(distance_matrix)
            
            # add delivery orders nodes to planned route (exclude the first node: driver.destination or current location)
            for tsp_index in visiting_sequence[1:]:
                location_id = all_locations_id[tsp_index]
                location = id_to_location.get(location_id)
                delivery_order_list = [o for o in carrying_orders if o.delivery_location_id == location_id]
                node = Node(location_id, location.lat, location.lng, [], delivery_order_list)
                driver_id_to_planned_route[driver_id].append(node) 
    
    # for the empty driver, it has been allocated to the order, but have not yet arrived at the pickup location (restaurant)
    pre_matching_order_ids = []
    for driver_id, driver in id_to_driver.items():
        # pickup orders from next destination
        if len(driver.carrying_orders) == 0 and driver.destination is not None:            
            pickup_orders = driver.destination.pickup_orders 
            pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders(pickup_orders, id_to_location)
            driver_id_to_planned_route[driver_id].extend(pickup_node_list)
            driver_id_to_planned_route[driver_id].extend(delivery_node_list)
            pre_matching_order_ids.extend([order.id for order in pickup_orders]) 
            
    # dispatch unallocated orders to drivers (largest capacity)
    driver_id_to_left_capacity = __get_left_capacity_of_driver(id_to_driver)
    for order_id, order in id_to_unallocated_order.items():
        # calculate the available drivers
        # available_driver_ids = [driver_id for driver_id, driver in id_to_driver.items() if driver_id_to_left_capacity[driver_id] > 0] 
        if order_id in pre_matching_order_ids:
            continue
        pickup_node_list, delivery_node_list = __create_pickup_and_delivery_nodes_of_orders([order], id_to_location)
        if pickup_node_list == [] or delivery_node_list == []:
            continue
        assign_driver_id = max(driver_id_to_left_capacity, key=driver_id_to_left_capacity.get)
        assign_driver = id_to_driver.get(assign_driver_id)
        driver_id_to_planned_route[assign_driver.id].extend(pickup_node_list)
        driver_id_to_planned_route[assign_driver.id].extend(delivery_node_list)
        driver_id_to_left_capacity[assign_driver_id] -= len(pickup_node_list)
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
       
    # create the output of the dispatch
    for driver_id, driver in id_to_driver.items():
        origin_planned_route = driver_id_to_planned_route.get(driver_id) # origin planned route include driver destination
        
        # Combine adjacent-duplicated nodes.
        __combine_duplicated_nodes(origin_planned_route)
        
        destination = None
        planned_route = []
        # determine the destination
        if driver.destination is not None:
            if len(origin_planned_route) == 0:
                logger.error(f"Planned route of driver {driver_id} is wrong")
            else:
                destination = origin_planned_route[0]
                destination.arrive_time = driver.destination.arrive_time
                planned_route = [origin_planned_route[i] for i in range(1, len(origin_planned_route))]
        elif len(origin_planned_route) > 0:
            destination = origin_planned_route[0]
            planned_route = [origin_planned_route[i] for i in range(1, len(origin_planned_route))]
        # set the destination and planned route
        driver_id_to_destination[driver_id] = destination
        driver_id_to_planned_route[driver_id] = planned_route
            
    return driver_id_to_destination, driver_id_to_planned_route
            

def __calculate_demand(order_list: list):
    demand = 0
    for order in order_list:
        demand += order.demand
    return demand


def __remove_adjacent_duplicate(location_list: list):
    i = 1
    while i < len(location_list):    
        if location_list[i] == location_list[i-1]:
            location_list.pop(i)
            i -= 1  
        i += 1
    return location_list
    

def __get_left_capacity_of_driver(id_to_driver: dict):
    '''
    Get driver left capacity
    Input:
    - id_to_driver: {driver_id: driver object}
    Output:
    - left capacity of each driver: {driver_id: left capacity}
    '''
    driver_id_to_left_capacity = {}
    for driver_id, driver in id_to_driver.items():
        carrying_orders = driver.carrying_orders
        left_capacity = driver.capacity
        for order in carrying_orders:
            left_capacity -= order.demand
        driver_id_to_left_capacity[driver_id] = left_capacity

    return driver_id_to_left_capacity
    

def __create_pickup_and_delivery_nodes_of_orders(orders: list, id_to_location: dict):
    '''
    Get the pickup and delivery nodes of orders
    Inputs:
    - orders: list of orders
    - id_location: dict, {location_id: location}
    Output:
    - pickup_node_list, delivery_node_list
    '''
    pickup_location_id_list = __get_pickup_location_id(orders)
    delivery_location_id_list = __get_delivery_location_id(orders)
    
    # order must have both pickup and delivery location
    if len(pickup_location_id_list) == 0 or len(delivery_location_id_list) == 0:
        return None, None

    # pickup node
    pickup_location_list = [] # 只有一个餐厅
    pickup_node_list = []
    for pickup_location_id in pickup_location_id_list:
        pickup_location = id_to_location.get(pickup_location_id)
        pickup_location_list.append(pickup_location)
        pickup_node = Node(pickup_location_id, pickup_location.lat, pickup_location.lng, copy.copy(orders), [])
        pickup_node_list.append(pickup_node)
    
    # delivery node
    delivery_location_list = []
    delivery_node_list = [] # 有多个顾客
    for index in range(len(delivery_location_id_list)):
        delivery_location_id = delivery_location_id_list[index]
        delivery_location = id_to_location.get(delivery_location_id)
        delivery_location_list.append(delivery_location)
        delivery_node = Node(delivery_location_id, delivery_location.lat, delivery_location.lng, [], [copy.copy(orders[index])])
        delivery_node_list.append(delivery_node)
    
    return pickup_node_list, delivery_node_list


def __get_pickup_location_id(orders):
    '''
    Get the pickup location id of orders
    订单的pickup location就是餐厅，如果orders来自同一个餐厅，那么所有orders的pickup location都一样
    Input:
    - orders: list of order object
    Output:
    - location_id: list of order pickup location id
    '''
    if len(orders) == 0:
        logger.error("Length of orders is 0")
        return ""

    location_id = []
    for order in orders:
        if order.pickup_location_id not in location_id:
            location_id.append(order.pickup_location_id)

    return location_id


def __get_delivery_location_id(orders):
    '''
    Get the delivery location id of orders
    订单的delivery location是顾客所在地，每个order的delivery location可以不一样
    '''
    if len(orders) == 0:
        logger.error("Length of orders is 0")
        return ""

    location_id = []
    for order in orders:
        if order.delivery_location_id not in location_id:
            location_id.append(order.delivery_location_id)

    return location_id


def __combine_duplicated_nodes(nodes):
    '''
    合并相邻重复节点 Combine adjacent-duplicated nodes.
    '''
    n = 0
    while n < len(nodes)-1:
        if nodes[n].id == nodes[n+1].id:
            nodes[n].pickup_orders.extend(nodes.pop(n+1).pickup_orders)
        n += 1





"""

Main body
# Note
# This is the demo to show the main flowchart of the algorithm

"""



def scheduling():
    '''
    派单算法执行程序
    '''

    # read the input json, you can design your own classes
    id_to_location, id_to_unallocated_order, id_to_ongoing_order, id_to_driver = __read_input_json()

    # dispatching algorithm
    driver_id_to_destination, driver_id_to_planned_route = dispatch_orders_to_drivers(
        id_to_unallocated_order,
        id_to_driver,
        id_to_location,
        )

    # output the dispatch result
    __output_json(driver_id_to_destination, driver_id_to_planned_route)
    

def __read_input_json():
    '''
    Read the information from json
    '''
    # read the restaurant & customer location info
    id_to_restaurant = get_restaurant_info(Configs.restaurant_info_file_path)
    id_to_customer = get_customer_info(Configs.customer_info_file_path)
    id_to_location = {**id_to_restaurant, **id_to_customer}

    # 未分配的订单
    unallocated_orders = read_json_from_file(Configs.algorithm_unallocated_orders_input_path)
    id_to_unallocated_order = get_order_dict(unallocated_orders, 'Order')

    # 已分配正在运送的订单
    ongoing_orders = read_json_from_file(Configs.algorithm_ongoing_orders_input_path)
    id_to_ongoing_order = get_order_dict(ongoing_orders, 'Order')
    
    # 总的订单
    id_to_order = {**id_to_unallocated_order, **id_to_ongoing_order}

    # 骑手信息
    driver_infos = read_json_from_file(Configs.algorithm_driver_input_info_path)
    id_to_driver = get_driver_instance_dict(driver_infos, id_to_order, id_to_location)

    return id_to_location, id_to_unallocated_order, id_to_ongoing_order,  id_to_driver


def __output_json(driver_id_to_destination, driver_id_to_planned_route):
    '''
    Output the dispatch result to data interaction fold
    '''
    # read json as dict first into a list, then append new dict and write back to json
    if os.path.getsize(Configs.algorithm_output_total_destination_path) == 0:
        total_dispatch_destination = []
    else:
        total_dispatch_destination = read_json_from_file(Configs.algorithm_output_total_destination_path)
    total_dispatch_destination.append(convert_nodes_to_json(driver_id_to_destination))
    write_json_to_file(Configs.algorithm_output_total_destination_path, total_dispatch_destination)
    
    # data interaction
    write_json_to_file(Configs.algorithm_output_destination_path, convert_nodes_to_json(driver_id_to_destination))
    write_json_to_file(Configs.algorithm_output_planned_route_path, convert_nodes_to_json(driver_id_to_planned_route))