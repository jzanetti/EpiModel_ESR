#!/bin/bash


create_model=true
run_model=false

num_models=10
region_names=("Counties_Manukau" "Auckland" "Northland" "Canterbury" "Capital_and_Coast")

source activate epimodel_esr

for region_name in "${region_names[@]}"
do

   cfg_path=/home/zhangs/Github/EpiModel_ESR/etc/cfg/cfg.$region_name.yml
   workdir_base=/tmp/epimodel_esr_v6.0/$region_name
   syspop_base_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_base.parquet
   syspop_diary_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_diaries.parquet
   syspop_address_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_location.parquet
   syspop_healthcare_path=/home/zhangs/Github/EpiModel_ESR/etc/test_data/$region_name/syspop_healthcare.parquet


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
            echo "Running iteration (run_model) $i"
            nohup python cli/run_model.py --run_model --run_vis --workdir ${workdir_base} --cfg ${cfg_path} --model_id $i >& $workdir_base/log.run_model_$i &
         done
   fi
done