FROM mariadb:11

ENV DB_PASSWORD=root
ENV DB_NAME=math

# This file is executed ONLY on first initialization
COPY prime_numbers.sql /docker-entrypoint-initdb.d/prime_numbers.sql

EXPOSE 3306
