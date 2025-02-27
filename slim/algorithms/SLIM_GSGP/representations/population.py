"""
Population Class for Evolutionary Computation using PyTorch.
"""
from slim.utils.utils import _evaluate_slim_individual
from joblib import Parallel, delayed

class Population:
    def __init__(self, population):
        """
        Initialize the Population with a list of individuals.

        Args:
            population: List of individuals in the population.
        """

        self.population = population
        self.size = len(population)
        self.nodes_count = sum([ind.nodes_count for ind in population])

    def calculate_semantics(self, inputs, testing=False):
        """
        Calculate the semantics for each individual in the population.

        Args:
            inputs: Input data for calculating semantics.
            testing: Boolean indicating if the calculation is for testing semantics.

        Returns:
            None
        """

        [
            individual.calculate_semantics(inputs, testing)
            for individual in self.population
        ]

        if testing:
            self.test_semantics = [
                individual.test_semantics for individual in self.population
            ]

        else:
            self.train_semantics = [
                individual.train_semantics for individual in self.population
            ]

    def __len__(self):
        """
        Return the size of the population.

        Returns:
            int: Size of the population.
        """
        return self.size

    def __getitem__(self, item):
        """
        Get an individual from the population by index.

        Args:
            item: Index of the individual to retrieve.

        Returns:
            Individual: The individual at the specified index.
        """
        return self.population[item]

    def evaluate_no_parall(self, ffunction, y, operator="sum"):
        """
         Evaluate the population using a fitness function.

        Args:
            ffunction: Fitness function to evaluate the individuals.
            y: Expected output (target) values as a torch tensor.
            operator: Operator to apply to the semantics ("sum" or "prod").

        Returns:
            None
        """
        [
            individual.evaluate(ffunction, y, operator=operator)
            for individual in self.population
        ]

        self.fit = [individual.fitness for individual in self.population]

    def evaluate(self, ffunction, y, operator="sum", n_jobs=1):
        """
         Evaluate the population using a fitness function.

        Args:
            ffunction: Fitness function to evaluate the individuals.
            y: Expected output (target) values as a torch tensor.
            operator: Operator to apply to the semantics ("sum" or "prod").

        Returns:
            None
        """
        fits = Parallel(n_jobs=n_jobs)(
            delayed(_evaluate_slim_individual)(individual, ffunction=ffunction, y=y, operator=operator
            ) for individual in self.population)

        self.fit = fits

        # Assign individuals' fitness
        [self.population[i].__setattr__('fitness', f) for i, f in enumerate(self.fit)]

