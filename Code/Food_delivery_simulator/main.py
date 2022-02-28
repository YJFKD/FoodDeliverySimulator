import traceback
import datetime
import numpy as np
import sys

from src.configuration.config import Configs
from src.simulator.simulator_api import simulate
from src.utils.log_utils import ini_logger, remove_file_handler_of_logging
from src.utils.input_utils import get_simple_data
from src.utils.logging_engine import logger
from src.utils.input_utils import get_route_map
from src.common.route import Map

if __name__ == "__main__":
    # empty the last run create dispatch destination & planned route json file
    open(Configs.algorithm_output_total_destination_path, 'w').close()
    open(Configs.algorithm_output_total_planned_route_path, 'w').close()
    
    # read route map for instance with same locations (restaurants + customers)
    code_to_route = get_route_map(Configs.route_info_file_path)
    logger.info(f"Get {len(code_to_route)} routes")
    route_map = Map(code_to_route)
    
    # if you want to traverse all instances, set the selected_instances to []
    selected_instances = Configs.selected_instances
    if selected_instances:
        test_instances = selected_instances
    else:
        test_instances = Configs.all_test_instances
    score_list = []
    
    for idx in test_instances:
        # Initial the log
        log_file_name = f"Log_{datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S')}.log"
        ini_logger(log_file_name)

        instance = "instance_%d" % idx
        logger.info(f"Start to run {Configs.medium_instance_folder_path}: {instance}") # need to update for different instance

        try:
            score = simulate(Configs.customer_info_file, Configs.restaurant_info_file, instance, route_map)
            score_list.append(score)
            logger.info(f"Score of {instance}: {score}")
        except Exception as e:
            logger.error("Failed to run simulator")
            logger.error(f"Error: {e}, {traceback.format_exc()}")
            score_list.append(sys.maxsize)

        # delete the log file
        remove_file_handler_of_logging(log_file_name)

    avg_score = np.mean(score_list)
    
    # display the results
    print(score_list)
    print(avg_score)
    print("Happy Ending")





