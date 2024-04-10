#!/bin/bash

num_runs=10
seed_infection=0
infection_time=[0,20]
region_name=gisborne
dhb_name=Tairawhiti

workdir_base=/tmp/epimodel_esr_v3.0/$dhb_name
syspop_base_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_base.parquet
syspop_diary_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_diaries.parquet
syspop_address_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_location.parquet
syspop_healthcare_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_healthcare.parquet


mkdir -p ${workdir_base}

export PYTHONPATH=/home/zhangs/Github/EpiModel_ESR

source activate epimodel_esr

# Run the script multiple times
for ((i=1; i<=num_runs; i++))
do
   echo "Running iteration $i"
   # echo "nohup python cli/run.py --workdir ${workdir_base}_$i --syspop_base_path ${syspop_base_path} --syspop_diary_path ${syspop_diary_path} --syspop_address_path ${syspop_address_path} --dhb_list ${dhb_list} >& $workdir_base/log_$i &"
   nohup python cli/run_model.py --workdir ${workdir_base}/ens_$i --syspop_base_path ${syspop_base_path} --syspop_diary_path ${syspop_diary_path} --syspop_address_path ${syspop_address_path} --syspop_healthcare_path ${syspop_healthcare_path} --dhb_list ${dhb_name} --sample_ratio 0.15 --seed_infection ${seed_infection} --infection_time ${infection_time} >& $workdir_base/log.$i &
done

