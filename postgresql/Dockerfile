FROM postgres:latest

ENV POSTGRES_USER cry_cry
ENV POSTGRES_PASSWORD cry_pass
ENV POSTGRES_DB cry_assignment

COPY cry-schema.sql /docker-entrypoint-initdb.d/

EXPOSE 5432