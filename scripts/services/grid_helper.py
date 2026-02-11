#~ scripts/services/grid_helper.py
import math
from multiprocessing import cpu_count

from django.db.models.lookups import Range
from scipy.special import expi
from typing import List, Tuple

class GridHelper:
    __number_of_cores: int
    __first_number: int
    __last_number: int
    __ranges: List[Tuple[int, int]]

    def __init__(self, number_of_cores, first_number, last_number):
        self.__number_of_cores = number_of_cores
        self.__first_number = first_number
        self.__last_number = last_number
        self.__ranges = []
        if self.__number_of_cores > cpu_count():
            self.__number_of_cores = cpu_count()
        elif self.__number_of_cores < 2:
            self.__number_of_cores = 2

    @staticmethod
    def _riemann_aprox(x: float) -> float:
        """
        Calculate the aproximation of the quantity of prime numbers less than x using Riemann aproximation.
        Relation: li(x) = Ei(ln x).
        """
        if x <= 1:
            return 0

        log_x = math.log(x)
        return expi(log_x)

    def _approx_sum_li_sqrt_over_odds(self, first_number: int | None = None, last_number: int | None = None) -> float:
        if first_number is None:
            first_number = self.__first_number
        if last_number is None:
            last_number = self.__last_number
        # Approximates sum_{n=a,a+2,...}^{b} li(sqrt(n))
        def F(t: float) -> float:
            return 0.5 * ((t ** 2) * self._riemann_aprox(t) - self._riemann_aprox(t ** 3))
        a = math.sqrt(first_number)
        b = math.sqrt(last_number)

        return F(b) - F(a)

    def _get_boundary_by_binary_search(self, primes_to_eval_per_core: float, first_number: int | None = None) -> int:
        if first_number is None:
            first_number = self.__first_number
        low = first_number
        high = self.__last_number
        while low <= high:
            middle = low + (high - low) // 2
            current_primes_to_eval = self._approx_sum_li_sqrt_over_odds(first_number, middle)
            if current_primes_to_eval <= primes_to_eval_per_core:
                low = middle + 1
            else:
                high = middle - 1
        if low % 2 != 0:
            low += 1

        return low

    def get_quantity_of_prime_numbers_between(self, a: int, b: int) -> int:
        return int(round(self._riemann_aprox(b) - self._riemann_aprox(a)))

    def get_optimized_size(self) -> int:
        return int(self.get_quantity_of_prime_numbers_between(self.__ranges[0][0], self.__ranges[0][1]) * 1.05)

    def split_ranges_equal_work(self):
        primes_to_eval = self._approx_sum_li_sqrt_over_odds()
        primes_to_eval_per_core = primes_to_eval / self.__number_of_cores
        boundary = self._get_boundary_by_binary_search(primes_to_eval_per_core)
        self.__ranges = [(self.__first_number, boundary)]
        for i in range(1, self.__number_of_cores - 1):
            first_number_of_range = boundary + 1
            boundary = self._get_boundary_by_binary_search(primes_to_eval_per_core, first_number_of_range)
            self.__ranges.append((first_number_of_range, boundary))
        self.__ranges.append((boundary + 1, self.__last_number))

    def get_number_of_cores(self) -> int:
        return self.__number_of_cores

    def get_first_number(self) -> int:
        return self.__first_number

    def get_last_number(self) -> int:
        return self.__last_number

    def get_ranges(self) -> List[Tuple[int, int]]:
        return self.__ranges

    def set_number_of_cores(self, number_of_cores: int):
        self.__number_of_cores = number_of_cores

    def set_first_number(self, first_number: int):
        self.__first_number = first_number

    def set_last_number(self, last_number: int):
        self.__last_number = last_number

    def set_ranges(self, ranges):
        self.__ranges = ranges

    def get_range_of_core(self, core_idx: int) -> Tuple[int, int]:
        return self.__ranges[core_idx]

    def get_index_of_range_of_core(self, core_idx: int) -> int:
        index = 0
        if core_idx > 0:
            previous_range = self.__ranges[core_idx - 1]
            index = self.get_quantity_of_prime_numbers_between(self.__first_number, previous_range[1]) + 1

        return index

    def get_iterator_optimized_size(self) -> int:
        return int((self.get_quantity_of_prime_numbers_between(self.__first_number, self.__last_number) / self.__number_of_cores) * 1.05)

    def get_iterator_range_of_core(self, core_idx: int) -> range:
        return range((core_idx * 2) + self.__first_number, self.__last_number, self.__number_of_cores * 2)