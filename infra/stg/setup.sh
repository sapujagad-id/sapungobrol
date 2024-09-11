#!/usr/bin/env bash

sudo docker volume create sapungobrol-db-stg || :
sudo docker network create sapungobrol-stg || :