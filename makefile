override CONDA=$(CONDA_BASE)/bin/mamba

install_env:
	$(CONDA) env create -f env.yml
	# $(CONDA) activate epimodel_esr & pip install -U -e git+https://github.com/projectmesa/mesa@main#egg=mesa

run_job:
	./run_job.bash