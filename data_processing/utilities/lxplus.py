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
# nodes via `getenv` en el .jdl de HTCondor, o via `#SBATCH --export=ALL` en
# el script de Slurm (segun el scheduler elegido). Esto reduce el numero de
# argumentos que hay que pasarle al ejecutable.
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


# ---------------------------------------------------------------------------
# HTCondor
# ---------------------------------------------------------------------------
# HTCondor resuelve el equivalente al array job de Slurm de forma nativa con
# `queue ... from args_processing.dat`: encola un job por cada linea del
# archivo y le pasa las columnas como variables ($(INPUT_FILE), $(LFN),
# $(OUTPUT_DIR)), sin necesidad de pasar n_jobs ni de parsear el archivo a
# mano dentro del job (a diferencia de Slurm, que necesita conocer n_jobs de
# antemano para `#SBATCH --array=1-N` y luego usar SLURM_ARRAY_TASK_ID + sed).
def _condor_resource_lines(condor_params):
    cpus, mem, disk, job_flavour = (
        utils.require_key(condor_params, k)
        for k in ("cpus", "mem", "disk", "job_flavour")
    )
    gpus = condor_params.get("gpus", 0)
    requirements = condor_params.get("requirements")

    lines = [
        f"request_cpus            = {cpus}",
        f"request_memory          = {mem}",
        f"request_disk            = {disk}",
    ]
    if gpus and int(gpus) > 0:
        lines.append(f"request_gpus            = {gpus}")
    lines.append(f'+JobFlavour             = "{job_flavour}"')
    if requirements:
        lines.append(f"requirements            = {requirements}")
    return "\n".join(lines)


def create_condor_processing_file(condor_params):
    os.makedirs("logs", exist_ok=True)
    name_file = "processing.jdl"
    exe = utils.require_key(condor_params, "executable_file")
    resource_lines = _condor_resource_lines(condor_params)

    with open(name_file, "w") as f:
        f.write(f"""universe                 = vanilla
executable              = {exe}
arguments               = "$(INPUT_FILE) $(LFN) $(OUTPUT_DIR)"
getenv                  = X509_USER_PROXY,EOS_OUTPUT_DIR,PROJECT_DIR,CONDA_ENV_NAME,PROCESSING_SCRIPT
should_transfer_files   = NO
output                  = logs/job_$(ClusterId)_$(ProcId).out
error                   = logs/job_$(ClusterId)_$(ProcId).err
log                     = logs/job_$(ClusterId)_$(ProcId).log
{resource_lines}
retry                   = 5
queue INPUT_FILE, LFN, OUTPUT_DIR from args_processing.dat
""")
        return name_file


def create_condor_convert_file(condor_params):
    os.makedirs("logs", exist_ok=True)
    name_file = "converting.jdl"
    exe = utils.require_key(condor_params, "executable_file")
    resource_lines = _condor_resource_lines(condor_params)

    with open(name_file, "w") as f:
        f.write(f"""universe                 = vanilla
executable              = {exe}
arguments               = "$(INPUT_FILE) $(OUTPUT_FILE)"
getenv                  = TREE_NAME,BRANCHES,MAX_JAGGED_LEN,PROJECT_DIR,CONDA_ENV_NAME
should_transfer_files   = NO
output                  = logs/job_$(ClusterId)_$(ProcId).out
error                   = logs/job_$(ClusterId)_$(ProcId).err
log                     = logs/job_$(ClusterId)_$(ProcId).log
{resource_lines}
retry                   = 5
queue INPUT_FILE, OUTPUT_FILE from args_conversion.dat
""")
        return name_file


# ---------------------------------------------------------------------------
# Slurm
# ---------------------------------------------------------------------------
# Slurm no tiene un equivalente nativo a `queue ... from file`, asi que aqui
# si necesitamos saber n_jobs de antemano para declarar el array
# (`#SBATCH --array=1-N`) y, dentro del job, usar SLURM_ARRAY_TASK_ID + sed
# para leer la linea que le toca a cada tarea del array.
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
