squeue -u zhangs -h -t pending,running,stopped -r | wc -l
scontrol show jobid -dd <jobid>
