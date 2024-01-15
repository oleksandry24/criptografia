docker rm $(docker stop $(docker ps -a -q)) 

docker-compose  -f docker-compose-python-psql.yml   build  --no-cache 

mkdir -p python/app/logs

docker-compose  -f docker-compose-python-psql.yml up --build