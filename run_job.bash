#!/bin/bash


create_model=false
run_model=true

workdir=/tmp/epimodel_esr_v7.0/2022
cfg_dir=/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/cfg
# data_dir=/home/zhangs/Github/EpiModel_ESR/etc/test_data
# data_dir=/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/data/2019

num_models=10
# region_names=("Counties_Manukau" "Auckland" "Canterbury" "Capital_and_Coast")
# region_names=("Northland")
region_names=("Counties_Manukau")

source activate epimodel_esr

for region_name in "${region_names[@]}"
do

   cfg_path=$cfg_dir/cfg.$region_name.yml
   workdir_base=$workdir/$region_name
   #syspop_base_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_base.parquet
   #syspop_diary_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_diaries.parquet
   #syspop_address_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_location.parquet
   #syspop_healthcare_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_healthcare.parquet


   mkdir -p ${workdir_base}

   export PYTHONPATH=/home/zhangs/Github/EpiModel_ESR

   if $create_model
   then
      for ((i=1; i<=num_models; i++))
         do
            echo "Running iteration (create_model) $region_name, $i"
            nohup python cli/run_model.py --create_model --workdir ${workdir_base} --cfg ${cfg_path} --model_id $i >& $workdir_base/log.create_model_$i &
         done
   fi

   if $run_model
   then
      for ((i=1; i<=num_models; i++))
         do
            echo "Running iteration (run_model) $region_name, $i"
            nohup python cli/run_model.py --run_model --run_vis --workdir ${workdir_base} --cfg ${cfg_path} --model_id $i >& $workdir_base/log.run_model_$i &
         done
   fi
done
