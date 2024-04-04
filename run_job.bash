#!/bin/bash

num_runs=10
workdir_base=/tmp/epimodel_esr
syspop_base_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/syspop_base.parquet
syspop_diary_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/syspop_diaries.parquet
syspop_address_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/syspop_location.parquet
dhb_list="Counties_Manukau"

export PYTHONPATH=/home/zhangs/Github/EpiModel_ESR

source activate epimodel_esr

# Run the script multiple times
for ((i=1; i<=num_runs; i++))
do
   echo "Running iteration $i"
   # echo "nohup python cli/run.py --workdir ${workdir_base}_$i --syspop_base_path ${syspop_base_path} --syspop_diary_path ${syspop_diary_path} --syspop_address_path ${syspop_address_path} --dhb_list ${dhb_list} >& $workdir_base/log_$i &"
   nohup python cli/run.py --workdir ${workdir_base}_$i --syspop_base_path ${syspop_base_path} --syspop_diary_path ${syspop_diary_path} --syspop_address_path ${syspop_address_path} --dhb_list ${dhb_list} >& $workdir_base/log.$i &
done

