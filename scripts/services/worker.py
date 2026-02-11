from .grid_helper import GridHelper
from .chronometer import Chronometer
from multiprocessing import shared_memory as shm
import math
import numpy as np
import time

class Worker:
    SHARED_MEMORY_NAME: str
    ARRAY_SHAPE: tuple

    def __init__(self, shared_memory_name: str, array_shape: tuple):
        #context.Thread.__init__(self)
        self.SHARED_MEMORY_NAME = shared_memory_name
        self.ARRAY_SHAPE = array_shape

    def calculate_prime_numbers(self, thread_id: int, prime_numbers: list, gridhelper: GridHelper, current_time: Chronometer):
        shared_memory_local = shm.SharedMemory(name=self.SHARED_MEMORY_NAME)
        try:
            shared_array_local = np.ndarray(self.ARRAY_SHAPE, dtype=np.int32, buffer=shared_memory_local.buf)
            shared_row_local = shared_array_local[thread_id - 1]
            initial_number, last_number = gridhelper.get_range_of_core(thread_id - 1)
            j = 0
            for number in range(initial_number, last_number, 2):
                sqrt_number = int(math.sqrt(number))
                i = 0
                prime_number = prime_numbers[i]
                is_prime = True
                while is_prime and prime_number < sqrt_number and prime_number < last_number:
                    is_prime = (number % prime_number != 0)
                    i += 1
                    prime_number = prime_numbers[i]
                if is_prime:
                    shared_row_local[j] = number
                    j += 1
            print("Thread-%d.\nQuantity of generated prime numbers: %d, time: %s"%(thread_id, j, current_time))
        finally:
            shared_memory_local.close()

    def calculate_prime_numbers_iterator(self, thread_id: int, prime_numbers: list, gridhelper: GridHelper, current_time: float):
        shared_memory_local = shm.SharedMemory(name=self.SHARED_MEMORY_NAME)
        try:
            shared_array_local = np.ndarray(self.ARRAY_SHAPE, dtype=np.int32, buffer=shared_memory_local.buf)
            shared_row_local = shared_array_local[thread_id - 1]
            range_of_core = gridhelper.get_iterator_range_of_core(thread_id - 1)
            last_number = gridhelper.get_last_number()
            j = 0
            for number in range_of_core:
                sqrt_number = int(math.sqrt(number))
                i = 0
                prime_number = prime_numbers[i]
                is_prime = True
                while is_prime and prime_number < sqrt_number and prime_number < last_number:
                    is_prime = (number % prime_number != 0)
                    i += 1
                    prime_number = prime_numbers[i]
                if is_prime:
                    shared_row_local[j] = number
                    j += 1
            print("Thread-%d.\nQuantity of generated prime numbers: %d, time: %s"%(thread_id, j, current_time))
        finally:
            shared_memory_local.close()