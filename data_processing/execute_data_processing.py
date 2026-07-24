import argparse
import os
import utilities.utils as utils
import utilities.lxplus as lxplus


def main(config_path):

    config = utils.load_config(config_path)
    proxy_config = utils.require_key(config, "proxy")
    gen_proxy = utils.require_key(proxy_config, "generate")
    processing_config = utils.require_key(config, "data_processing")

    # "cms_das" (default, comportamiento actual via DAS) o
    # "open_data" (archivos ROOT locales ya copiados al cluster, sin DAS).
    input_mode = processing_config.get("input_mode", "cms_das")
    if input_mode not in ("cms_das", "open_data"):
        raise ValueError(
            f"input_mode invalido: '{input_mode}' (valores permitidos: 'cms_das', 'open_data')"
        )

    # "condor" (default, HTCondor via `queue ... from args_processing.dat`) o
    # "slurm" (array job via `#SBATCH --array`).
    scheduler = processing_config.get("scheduler", "condor")
    if scheduler not in ("condor", "slurm"):
        raise ValueError(
            f"scheduler invalido: '{scheduler}' (valores permitidos: 'condor', 'slurm')"
        )

    datasets = utils.require_key(processing_config, "datasets")
    eos_output_dir = utils.require_key(processing_config, "eos_output_dir")
    conda_env = utils.require_key(processing_config, "conda_env")
    scheduler_params = utils.require_key(
        processing_config, "condor_params" if scheduler == "condor" else "slurm_params"
    )
    processing_script = utils.require_key(processing_config, "processing_script")

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if input_mode == "cms_das":
        if gen_proxy == 1:
            lxplus.generate_proxy(proxy_config)

        proxy_path = utils.require_key(proxy_config, "proxy_path")
        proxy_path = lxplus.expand_proxy_path(proxy_path)
    else:
        # El modo open_data no necesita proxy de grid: no se consulta DAS
        # ni se accede a eospublic.cern.ch, solo archivos locales.
        proxy_path = ""

    lxplus.set_env_vars_processing(
        proxy_path, eos_output_dir, project_dir, conda_env, processing_script
    )

    if input_mode == "cms_das":
        redirector = utils.require_key(processing_config, "redirector")
        datasets = lxplus.das_query_endpoints(redirector, datasets)
        args_dat, mapping = lxplus.build_args_cms_das(datasets, eos_output_dir)
    else:
        datasets = lxplus.resolve_open_data_files(datasets)
        args_dat, mapping = lxplus.build_args_open_data(datasets, eos_output_dir)

    utils.write_args_file("args_processing.dat", args_dat)

    utils.write_map_file("mapping.json", mapping)

    if scheduler == "condor":
        name_file = lxplus.create_condor_processing_file(scheduler_params)
        utils.submit_condor(name_file)
    else:
        name_file = lxplus.create_slurm_processing_script(scheduler_params, len(args_dat))
        utils.submit_slurm(name_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processing NanoAOD root files")
    parser.add_argument(
        "-f", "--file", type=str, help="Path to the configuration file.", required=True
    )
    args = parser.parse_args()

    main(args.file)
