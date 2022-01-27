#!/bin/bash

export email=$(cat ~/.config/screeps/.email)
export password=$(cat ~/.config/screeps/.pw)

python screepscli.py log
