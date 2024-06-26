override CONDA=$(CONDA_BASE)/bin/mamba

install_env:
	$(CONDA) env create -f env.yml
	# $(CONDA) activate epimodel_esr & pip install -U -e git+https://github.com/projectmesa/mesa@main#egg=mesa

run_job:
	./run_job.bash

kill_job:
	pkill -9 -f "cli/run_model.py"

run_sensitivity_job:
	nohup python etc/submit/others/run_job_sensitivity.py >& run_job_sensitivity.log &