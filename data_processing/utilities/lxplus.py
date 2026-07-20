import os
import sys
import utilities.utils as utils


def expand_proxy_path(path):
    path = os.path.expandvars(os.path.expanduser(path))
    path = path.replace("$(id -u)", str(os.getuid()))
    return path


def generate_proxy(proxy_config):
    proxy_path = utils.require_key(proxy_config, "proxy_path")
    proxy_path = expand_proxy_path(proxy_path)

    cmd = [
        "voms-proxy-init",
        "--voms",
        utils.require_key(proxy_config, "voms"),
        "--rfc",
        "--valid",
        utils.require_key(proxy_config, "proxy_time"),
        "--out",
        proxy_path,
    ]

    utils.exe_cmd(cmd, allow_tty_mode=True)
    os.environ["X509_USER_PROXY"] = proxy_path
    print(
        f"\nTo set env varible in current shell execute: export X509_USER_PROXY={proxy_path}"
    )


def das_query_endpoints(redirector, datasets):
    for dataset in datasets:
        LFN = utils.require_key(dataset, "LFN")
        ID = utils.require_key(dataset, "ID")
        amount = utils.require_key(dataset, "amount")

        cmd = ["dasgoclient", "-query", f"file dataset={LFN}"]

        if amount == -1:
            files = utils.exe_cmd(cmd).splitlines()
        else:
            files = utils.exe_cmd(cmd).splitlines()[:amount]

        endpoints = [f"root://{redirector}/{f}" for f in files]
        dataset["endpoints"] = endpoints
    return datasets


def resolve_open_data_files(datasets):
    """
    Resuelve datasets para input_mode == 'open_data'.

    A diferencia de das_query_endpoints, esta funcion NO consulta DAS: los
    archivos ROOT ya estan disponibles localmente. Cada dataset debe traer
    exactamente una de estas dos opciones:

      - 'files': lista explicita de rutas a archivos .root
      - 'path':  carpeta local; se toman todos los *.root que contenga
                 (no recursivo)

    Devuelve los datasets con 'files' ya resuelto, listos para que
    build_args_open_data genere args_processing.dat.
    """
    for dataset in datasets:
        name = utils.require_key(dataset, "name")
        utils.require_key(dataset, "ID")
        files = dataset.get("files")
        path = dataset.get("path")

        if files and path:
            raise ValueError(
                f"Dataset '{name}' (open_data): especifica 'files' o 'path', no ambos."
            )

        if path:
            found = sorted(
                os.path.join(path, f) for f in os.listdir(path) if f.endswith(".root")
            )
            if not found:
                raise ValueError(
                    f"Dataset '{name}' (open_data): no se encontraron archivos .root en '{path}'."
                )
            dataset["files"] = found
        elif not files:
            raise ValueError(
                f"Dataset '{name}' (open_data) no tiene 'files' ni 'path'."
            )

    return datasets


def build_args_cms_das(datasets, eos_output_dir):
    """Construye args_processing.dat y mapping.json para input_mode == 'cms_das'."""
    args_dat = []
    mapping = {}
    for dataset in datasets:
        LFN = dataset["LFN"]
        ID = dataset["ID"]
        endpoints = dataset["endpoints"]
        dataset_dir = f"{eos_output_dir}/{utils.path_to_dir_name(LFN)}"

        os.makedirs(dataset_dir, exist_ok=True)

        for endpoint in endpoints:
            args_dat.append(f"{endpoint}, {LFN}, {dataset_dir}")

        mapping[ID] = LFN

    return args_dat, mapping


def build_args_open_data(datasets, eos_output_dir):
    """Construye args_processing.dat y mapping.json para input_mode == 'open_data'."""
    args_dat = []
    mapping = {}
    for dataset in datasets:
        name = dataset["name"]
        ID = dataset["ID"]
        files = dataset["files"]
        dataset_dir = f"{eos_output_dir}/{utils.path_to_dir_name(name)}"

        os.makedirs(dataset_dir, exist_ok=True)

        for f in files:
            args_dat.append(f"{f}, {name}, {dataset_dir}")

        mapping[ID] = name

    return args_dat, mapping


# This function sets env variables that will be transferred to the worker
# nodes via `#SBATCH --export=ALL` in el script de Slurm. Esto reduce el
# numero de argumentos que hay que pasarle al ejecutable.
#
# Nota: ya no se necesita AFS_CMS_BASE / empaquetar un area de CMSSW, porque
# run_filter.sh ahora usa mini_nanotools (PyROOT puro) en vez de
# PhysicsTools.NanoAODTools, y por lo tanto no requiere `cmsenv`/scram.
def set_env_vars_processing(
    proxy_path, eos_output_dir, project_dir, conda_env, processing_script
):
    os.environ["X509_USER_PROXY"] = proxy_path
    os.environ["EOS_OUTPUT_DIR"] = eos_output_dir
    os.environ["PROJECT_DIR"] = project_dir
    os.environ["CONDA_ENV_NAME"] = conda_env
    os.environ["PROCESSING_SCRIPT"] = processing_script


def set_env_vars_conversion(tree_name, branches, max_jagged_len, project_dir, conda_env):
    os.environ["TREE_NAME"] = tree_name
    os.environ["BRANCHES"] = (
        ",".join(branches) if isinstance(branches, list) else str(branches)
    )
    os.environ["MAX_JAGGED_LEN"] = str(max_jagged_len)
    os.environ["PROJECT_DIR"] = project_dir
    os.environ["CONDA_ENV_NAME"] = conda_env


def _slurm_resource_lines(slurm_params):
    cpus, gpus, mem, time = (
        utils.require_key(slurm_params, k) for k in ("cpus", "gpus", "mem", "time")
    )
    partition = slurm_params.get("partition")

    lines = [
        f"#SBATCH --cpus-per-task={cpus}",
        f"#SBATCH --mem={mem}",
        f"#SBATCH --time={time}",
    ]
    if gpus and int(gpus) > 0:
        lines.append(f"#SBATCH --gres=gpu:{gpus}")
    if partition:
        lines.append(f"#SBATCH --partition={partition}")
    return "\n".join(lines)


def create_slurm_processing_script(slurm_params, n_jobs):
    os.makedirs("logs", exist_ok=True)
    name_file = "processing.slurm"
    exe = utils.require_key(slurm_params, "executable_file")
    resource_lines = _slurm_resource_lines(slurm_params)

    with open(name_file, "w") as f:
        f.write(f"""#!/bin/bash
#SBATCH --job-name=cms_processing
#SBATCH --array=1-{n_jobs}
{resource_lines}
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err
#SBATCH --export=ALL
 
LINE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" args_processing.dat)
IFS=',' read -r INPUT_FILE LFN OUTPUT_SUBDIR <<< "$LINE"
INPUT_FILE=$(echo "$INPUT_FILE" | xargs)
LFN=$(echo "$LFN" | xargs)
OUTPUT_SUBDIR=$(echo "$OUTPUT_SUBDIR" | xargs)
 
bash {exe} "$INPUT_FILE" "$LFN" "$OUTPUT_SUBDIR"
""")
        return name_file


def create_slurm_convert_script(slurm_params, n_jobs):
    os.makedirs("logs", exist_ok=True)
    name_file = "converting.slurm"
    exe = utils.require_key(slurm_params, "executable_file")
    resource_lines = _slurm_resource_lines(slurm_params)

    with open(name_file, "w") as f:
        f.write(f"""#!/bin/bash
#SBATCH --job-name=cms_h5_conversion
#SBATCH --array=1-{n_jobs}
{resource_lines}
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err
#SBATCH --export=ALL
 
LINE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" args_conversion.dat)
read -r INPUT_FILE OUTPUT_FILE <<< "$LINE"
 
bash {exe} "$INPUT_FILE" "$OUTPUT_FILE"
""")
        return name_file
