#
# Authors: Nuno Antunes <nmsa@dei.uc.pt>, João Antunes <jcfa@dei.uc.pt>
#

FROM postgres:latest


ENV POSTGRES_USER ddss-database-assignment-2
ENV POSTGRES_PASSWORD ddss-database-assignment-2
ENV POSTGRES_DB ddss-database-assignment-2

COPY ddss-db-schema-pg.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
