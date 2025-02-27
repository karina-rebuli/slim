"""
This script runs the StandardGSGP algorithm on various datasets and configurations,
logging the results for further analysis.
"""

import uuid
import os
from slim.algorithms.GSGP.gsgp import GSGP
from slim.config.gsgp_config import *
from slim.utils.logger import log_settings
from slim.utils.utils import get_terminals, validate_inputs, generate_random_uniform, validate_functions_dictionary, validate_constants_dictionary
from typing import Callable

# todo: would not be better to first log the settings and then perform the algorithm?
def gsgp(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor = None, y_test: torch.Tensor = None,
         dataset_name: str = None, pop_size: int = 100, n_iter: int = 100, p_xo: float = 0.0, elitism: bool = True,
         n_elites: int = 1, init_depth: int = 8, ms_lower: float = 0, ms_upper: float = 1,
         log_path: str = os.path.join(os.getcwd(), "log", "gsgp.csv"),
         seed: int = 1,
         log: int = 1,
         verbose: int = 1,
         reconstruct: bool = False,
         fitness_function: str = "rmse",
         initializer: str = "rhh",
         minimization: bool = True,
         prob_const: float = 0.2,
         tree_functions: dict = FUNCTIONS,
         tree_constants: dict = CONSTANTS,
         n_jobs: int = 1):
    """
    Main function to execute the Standard GSGP algorithm on specified datasets

    Parameters
    ----------
    X_train: (torch.Tensor)
        Training input data.
    y_train: (torch.Tensor)
        Training output data.
    X_test: (torch.Tensor), optional
        Testing input data.
    y_test: (torch.Tensor), optional
        Testing output data.
    dataset_name : str, optional
        Dataset name, for logging purposes
    pop_size : int, optional
        The population size for the genetic programming algorithm (default is 100).
    n_iter : int, optional
        The number of iterations for the genetic programming algorithm (default is 100).
    p_xo : float, optional
        The probability of crossover in the genetic programming algorithm. Must be a number between 0 and 1 (default is 0.8).
    elitism : bool, optional
        Indicate the presence or absence of elitism.
    n_elites : int, optional
        The number of elites.
    init_depth : int, optional
        The depth value for the initial GP trees population.
    ms : Callable, optional
        A function that will generate the mutation step
    log_path : str, optional
        The path where is created the log directory where results are saved.
    seed : int, optional
        Seed for the randomness


    Returns
    -------
       Tree
        Returns the best individual at the last generation.
    """

    validate_inputs(X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test,
                    pop_size=pop_size, n_iter=n_iter, elitism=elitism, n_elites=n_elites, init_depth=init_depth,
                    log_path=log_path, prob_const=prob_const)

    # TODO: verify this
    # verifying that the given tree functions and tree constants dictionaries are valid
    if tree_functions != FUNCTIONS:
        validate_functions_dictionary(tree_functions)
    if tree_constants != CONSTANTS:
        validate_constants_dictionary(tree_constants)

    # Checking that both ms bounds are numerical
    assert isinstance(ms_lower, (int, float)) and isinstance(ms_upper, (int, float)), \
        "Both ms_lower and ms_upper must be either int or float"
    # If so, create the ms callable
    ms = generate_random_uniform(ms_lower, ms_upper)

    # assuring the p_xo is valid
    assert 0 <= p_xo <= 1, "p_xo must be a number between 0 and 1"

    # assuring the prob_const is valid
    assert 0 <= prob_const <= 1, "prob_const must be a number between 0 and 1"

    # creating a list with the valid available fitness functions
    valid_fitnesses = list(fitness_function_options)

    # assuring the chosen fitness_function is valid
    assert fitness_function.lower() in fitness_function_options.keys(), \
                    "fitness function must be: "+f"{', '.join(valid_fitnesses[:-1])} or {valid_fitnesses[-1]}"\
                                                                    if len(valid_fitnesses) > 1 else valid_fitnesses[0]

    # creating a list with the valid available initializers
    valid_initializers = list(initializer_options)

    # assuring the chosen initializer is valid
    assert initializer.lower() in initializer_options.keys(), \
        "initializer must be " + f"{', '.join(valid_initializers[:-1])} or {valid_initializers[-1]}" \
                                                            if len(valid_initializers) > 1 else valid_initializers[0]

    # setting the number of elites to 0 if no elitism is used
    if not elitism:
        n_elites = 0

    # getting a unique run id for the settings logging
    unique_run_id = uuid.uuid1()

    # setting the algorithm name to standard gsgp for logging TODO: do I add this as a changeable thing?
    algo_name = "StandardGSGP"

    # getting the terminals based on the training data
    TERMINALS = get_terminals(X_train)
    gsgp_pi_init["TERMINALS"] = TERMINALS
    gsgp_pi_init["FUNCTIONS"] = tree_functions
    gsgp_pi_init["CONSTANTS"] = tree_constants

    # setting up the information of the run, for logging purposes
    gsgp_solve_parameters["run_info"] = [algo_name, unique_run_id, dataset_name]

    # setting up the configuration dictionaries based on the user given input

    # GSGP PI_INIT DICTIONARY #
    gsgp_pi_init["init_pop_size"] = pop_size
    gsgp_pi_init["init_depth"] = init_depth
    gsgp_pi_init["p_c"] = prob_const

    # GSGP PARAMETERS DICTIONARY #
    gsgp_parameters["p_xo"] = p_xo
    gsgp_parameters["p_m"] = 1 - gsgp_parameters["p_xo"]
    gsgp_parameters["pop_size"] = pop_size
    gsgp_parameters["ms"] = ms

    gsgp_parameters["initializer"] = initializer_options[initializer]
    # TODO: probably remove this option since maximization doesnt make sense here... but it will in classification...
    if minimization:
        gsgp_parameters["selector"] = tournament_selection_min(2)
        gsgp_parameters["find_elit_func"] = get_best_min
    else:
        gsgp_parameters["selector"] = tournament_selection_max(2)
        gsgp_parameters["find_elit_func"] = get_best_max

    # GSGP SOLVE PARAMETERS DICTIONARY #

    gsgp_solve_parameters["n_iter"] = n_iter
    gsgp_solve_parameters["log_path"] = log_path
    gsgp_solve_parameters["elitism"] = elitism
    gsgp_solve_parameters["n_elites"] = n_elites
    gsgp_solve_parameters["n_jobs"] = n_jobs

    if X_test is not None and y_test is not None:
        gsgp_solve_parameters["test_elite"] = True
    else:
        gsgp_solve_parameters["test_elite"] = False

    gsgp_solve_parameters["log"] = log
    gsgp_solve_parameters["verbose"] = verbose
    gsgp_solve_parameters["reconstruct"] = reconstruct

    gsgp_solve_parameters["ffunction"] = fitness_function_options[fitness_function]

    optimizer = GSGP(pi_init=gsgp_pi_init, **gsgp_parameters, seed=seed)

    optimizer.solve(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        curr_dataset=dataset_name,
        **gsgp_solve_parameters,
    )

    log_settings(
        path=log_path[:-4] + "_settings.csv",
        settings_dict=[gsgp_solve_parameters,
                       gsgp_parameters,
                       gsgp_pi_init,
                       settings_dict],
        unique_run_id=unique_run_id,
    )
    return optimizer.elite


if __name__ == "__main__":
    from slim.datasets.data_loader import load_merged_data
    from slim.utils.utils import train_test_split

    X, y = load_merged_data("resid_build_sale_price", X_y=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, p_test=0.4)
    X_val, X_test, y_val, y_test = train_test_split(X_test, y_test, p_test=0.5)

    final_tree = gsgp(X_train=X_train, y_train=y_train,
                      X_test=X_val, y_test=y_val,
                      dataset_name='resid_build_sale_price', pop_size=100, n_iter=1000, log_path=os.path.join(os.getcwd(),
                                                                "log", f"TESTING_GSGP.csv"), fitness_function="rmse", n_jobs=2)

    predictions = final_tree.predict(X_test)
    print(float(rmse(y_true=y_test, y_pred=predictions)))
