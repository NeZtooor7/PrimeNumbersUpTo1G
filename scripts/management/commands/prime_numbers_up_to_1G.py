#~ scripts/management/commands/prime_numbers_up_to_1G.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from multiprocessing import shared_memory as shm, cpu_count, get_context
from scripts.models import PrimeNumbers
from scripts.services.grid_helper import GridHelper
from scripts.services.worker import Worker
from scripts.services.chronometer import Chronometer
from typing import List
import math
import numpy as np
import random

class Command(BaseCommand):
    LAST_NUMBER = 1_000_000_000
    SHARED_MEMORY_NAME = "shared_memory_array"
    ARRAY_SIZE = 0
    NUMBER_OF_CORES = cpu_count()

    def _show_random_prime_numbers(self, shared_array: np.ndarray):
        i = 0
        prime_numbers_to_show_list = []
        while i < 200:
            random_i = random.randint(0, self.ARRAY_SIZE - 1)
            random_j = random.randint(0, 7)
            if shared_array[random_j, random_i] != 0:
                prime_numbers_to_show_list.append(int(shared_array[random_j, random_i]))
                i += 1
        self.stdout.write("List of 200 generated prime numbers -> %s" % prime_numbers_to_show_list)

    @staticmethod
    def _save_bulk(prime_numbers_to_save: List[PrimeNumbers], size_of_bulk: int):
        PrimeNumbers.objects.bulk_create(
            prime_numbers_to_save,
            batch_size=size_of_bulk,
            ignore_conflicts=True,
        )
        prime_numbers_to_save.clear()

    def _save_all_prime_numbers(self, shared_array: np.ndarray, initial_number: int):
        last_prime = initial_number
        size_of_list_to_save = 10_000
        for i in range(self.NUMBER_OF_CORES):
            j = 0
            shared_row = shared_array[i]
            prime_numbers_to_save = []
            while shared_row[j] != 0 and j < self.ARRAY_SIZE:
                prime_numbers_to_save.append(
                    PrimeNumbers(
                        number = shared_row[j],
                        is_mersenne = math.log2(shared_row[j] + 1).is_integer(),
                        space_between_last_prime = shared_row[j] - last_prime,
                        created_at = timezone.now(),
                        updated_at = timezone.now(),
                    ))
                last_prime = shared_row[j]
                j += 1
                if j % size_of_list_to_save == 0 or j == self.ARRAY_SIZE:
                    self._save_bulk(prime_numbers_to_save, size_of_list_to_save)
            if prime_numbers_to_save:
                self._save_bulk(prime_numbers_to_save, size_of_list_to_save)

    def add_arguments(self, parser):
        parser.add_argument(
            "--equal-iteration-option",
            action="store_true",
            dest="equal_iteration_option",
            help="Every thread are going to use an iterator and evaluate numbers in the whole given range, but the numbers are going to be unsorted saved."
        )
        parser.add_argument(
            "--show-random-prime-numbers",
            action="store_true",
            dest="show_random_prime_numbers",
            help="Show 200 random generated prime numbers after the thread processing."
        )
        parser.add_argument(
            "--last-number",
            type=int,
            dest="last_number",
            help="Upper bound for prime calculation.",
        )

    def handle(self, *args, **options):
        prime_numbers = list(PrimeNumbers.objects
                .filter(number__gt=2)
                .order_by('number')
                .values_list('number', flat=True))
        initial_number = prime_numbers[-1] + 2
        if options["last_number"] is not None:
            if 50_000 <= options["last_number"] <= self.LAST_NUMBER:
                self.LAST_NUMBER = options["last_number"]
            elif options["last_number"] < 50_000:
                self.stdout.write("The given last number cannot be lesser than 50.000.")
                exit()
            elif options["last_number"] > self.LAST_NUMBER:
                self.stdout.write("The given last number cannot be greater than 1.000.000.000.")
                exit()
        #~ Setting the grid helper.
        gridhelper = GridHelper(self.NUMBER_OF_CORES, initial_number, self.LAST_NUMBER)
        if not options["equal_iteration_option"]:
            gridhelper.split_ranges_equal_work()
            self.ARRAY_SIZE = gridhelper.get_optimized_size()
        else:
            self.ARRAY_SIZE = gridhelper.get_iterator_optimized_size()
        #~ Setting shared memory objects.
        array_shape = (self.NUMBER_OF_CORES, self.ARRAY_SIZE)
        nbytes = int(np.prod(array_shape) * np.dtype(np.int32).itemsize)
        shared_memory = shm.SharedMemory(create=True, size=nbytes, name=self.SHARED_MEMORY_NAME)
        shared_array = np.ndarray(array_shape, dtype=np.int32, buffer=shared_memory.buf)
        shared_array.fill(0)
        #~ Start.
        current_time = Chronometer()
        context = get_context("spawn")
        threads = []
        #~ Creating all the threads.
        worker = Worker(self.SHARED_MEMORY_NAME, array_shape)
        method_worker = worker.calculate_prime_numbers
        if options["equal_iteration_option"]:
            method_worker = worker.calculate_prime_numbers_iterator
        for thread_id in range(1, self.NUMBER_OF_CORES + 1):
            thread = context.Process(target=method_worker, args=(thread_id, prime_numbers, gridhelper, current_time))
            thread.start()
            threads.append(thread)
        #~ Waiting for all of them.
        for thread in threads:
            thread.join()
        #~ The end.
        for thread in threads:
            thread.terminate()
        self.stdout.write("Total time: %s"%current_time)
        #~ Now show 200 random prime numbers.
        if options["show_random_prime_numbers"]:
            self._show_random_prime_numbers(shared_array)
        #~ Save all the prime numbers in database.
        self.stdout.write("Saving records in database.")
        current_time = Chronometer()
        self._save_all_prime_numbers(shared_array, initial_number - 2)
        self.stdout.write("Saving time: %s"%current_time)
        #~ unlink shared memory.
        shared_memory.close(); shared_memory.unlink()