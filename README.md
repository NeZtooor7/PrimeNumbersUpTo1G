# Prime Numbers Up To 1G (Parallel Version)

## Overview

This project is a **command-line program created in Django** that computes prime numbers using the successive divisions (trial division) algorithm in a parallelized architecture.

Its objectives are:

- Compute prime numbers up to a configurable upper bound (default: 1,000,000,000)
- Distribute computation across multiple CPU cores
- Store discovered prime numbers efficiently in a MariaDB database
- Optimize workload distribution using a Riemann-based approximation model

---

## Algorithm: Successive Divisions (Trial Division)

The successive divisions algorithm determines whether a number `n` is prime by:

1. Taking all known prime numbers `p` such that `p ≤ sqrt(n)`
2. Dividing `n` by each of these primes
3. If no division produces remainder 0 → `n` is prime

If `n = a × b`, then at least one of `a` or `b` must be ≤ `sqrt(n)`.  
Therefore, checking divisibility up to `sqrt(n)` is sufficient.

---

## Why primes from 2 to 31627 are the base

We use prime numbers from:

```
2 → 31627
```

Because:

```
√(1,000,000,000) ≈ 31622
```

To test any number up to 1,000,000,000, we only need prime divisors up to its square root.

So primes up to ~31627 form the base set for computing:

```
31629 → 1,000,000,000
```

---

## Why This Version Is Parallel

The sequential trial division approach becomes extremely slow for large ranges.

This version:

- Splits the search range into subranges
- Assigns each subrange to a CPU core
- Runs workers in parallel
- Saves results in batches

### Why not use the Sieve (Criba) algorithm?

The Sieve of Eratosthenes is very efficient for generating primes in a fixed range because it marks multiples in a shared array.

However:

- It requires heavily shared memory
- Parallelization is complex due to overlapping writes
- Memory usage becomes very large for 1,000,000,000

Trial division allows independent evaluation per number, making it more practical for this scalable parallel architecture.

---

## Database Setup

### Option 1: Local MariaDB/MySQL

1. Install MariaDB or MySQL
2. Create database:

```
math
```

3. Preload primes (2 to 31627) before first execution:

```
mysql -u root -p math < prime_numbers.sql
```

4. Configure `.env`:

```
DB_NAME=math
DB_USER=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3307
```

---

### Option 2: Docker

Run the Dockerfile located in `docker/mariadb-math` to load the virtual database and environment.

From the project root:

```
docker build -t mariadb-math docker/mariadb-math
docker run -p 3307:3306 mariadb-math
```
Then configure the `.env` file accordingly to connect to the running container.

---

## Installation

```
pip install -r requirements.txt
python manage.py migrate
```

---

## Running the Computation

Default:

```
python manage.py prime_numbers_up_to_1G
```

Custom upper bound:

```
python manage.py prime_numbers_up_to_1G --last-number=50000
```

Show 200 random primes:

```
python manage.py prime_numbers_up_to_1G --show-random-prime-numbers
```

Equal iteration mode:

```
python manage.py prime_numbers_up_to_1G --equal-iteration-option
```

### Command Line Options

```
--last-number=x
--show-random-prime-numbers
--equal-iteration-option
```

---

## Range Splitting Strategies

### Default Mode (Recommended)

Uses:

```
split_ranges_equal_work
```

This strategy balances computational workload per thread by estimating the real computational cost of evaluating each number, not just counting how many numbers exist in a range.

For each number n, the cost of evaluating primality is proportional to the number of prime divisors that must be tested, which is approximately the number of primes ≤ √n.

Using the Riemann approximation, this quantity is estimated via the logarithmic integral:

```
li(√n)
```

Since:

```
π(x) ≈ li(x)
```
where π(x) is the prime-counting function, the algorithm approximates the number of prime divisions required for each candidate number using:

```
li(√n)
```

The accumulated sum of these approximations over a subrange provides an estimate of the total computational work for that range.

`split_ranges_equal_work` then:

- Computes the cumulative estimated workload across the full interval
- Divides it into equal portions (one per core)
- Generates ranges so each thread receives approximately the same total estimated division cost

This results in:
- Better CPU balance
- Reduced idle time between threads
- Prime numbers saved in natural numeric order

---

### Equal Iteration Option

Activated with:

```
--equal-iteration-option
```

Each thread evaluates alternating numbers between 31629 and the upper bound.

Example with 2 cores:

Thread 1:
```
31629, 31633, 31637, ..., 999999997
```

Thread 2:
```
31631, 31635, 31639, ..., 999999999
```

For more cores, distribution is automatically calculated by `GridHelper`.

This ensures more equal execution time per thread but does not preserve insertion order.

---

## Summary

This project demonstrates:

- Mathematical correctness via trial division
- Intelligent workload balancing using Riemann approximation
- Parallel CPU utilization
- Efficient database persistence
- Clean separation of computation and persistence layers

### Performance Notes

- Bulk inserts (batch size 1000)
- Shared memory between processes
- UTC timestamp storage
- Default splitting gives better CPU balance
- Equal iteration provides deterministic distribution

This is both a mathematical and architectural experiment in scalable prime computation.
