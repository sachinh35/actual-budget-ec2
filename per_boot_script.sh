#!/bin/bash

sudo service docker start
cd /home/ec2-user/actual_budget
docker-compose up --detach