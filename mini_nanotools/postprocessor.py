import array
import json
import os
import re

import ROOT

from .datamodel import Event, _COUNTER_RE

_ALWAYS_ACTIVE = ("run", "luminosityBlock", "event")

_TYPE_MAP = {
    "F": ("f", "F"),  # float
    "D": ("d", "D"),  # double
    "I": ("i", "I"),  # int
    "i": ("I", "i"),  # unsigned int
    "O": ("b", "O"),  # bool (almacenado como byte)
    "L": ("l", "L"),  # long
    "l": ("L", "l"),  # unsigned long
}


class WrappedOutputTree(object):
    """Envuelve un TTree de salida, permitiendo declarar ramas nuevas y
    llenarlas por evento, igual que en NanoAODTools:

        self.out.branch("nombre", "F")
        ...
        self.out.fillBranch("nombre", valor)

    """

    _INT_DTYPES = ("I", "i", "O", "L", "l")

    def __init__(self, tree):
        self._tree = tree
        self._buffers = {}
        self._dtypes = {}

    def branch(self, name, dtype="F", lenVar=None, title=None):
        if lenVar is not None:
            raise NotImplementedError(
                "WrappedOutputTree no soporta ramas de largo variable "
                "(lenVar='%s'). Declara una rama escalar por elemento." % lenVar
            )
        if dtype not in _TYPE_MAP:
            raise ValueError(
                "Tipo de rama '%s' no soportado. Tipos validos: %s"
                % (dtype, ", ".join(_TYPE_MAP))
            )
        typecode, leafcode = _TYPE_MAP[dtype]
        buf = array.array(typecode, [0])
        self._buffers[name] = buf
        self._dtypes[name] = dtype
        self._tree.Branch(name, buf, "%s/%s" % (name, leafcode))

    def fillBranch(self, name, value):
        try:
            buf = self._buffers[name]
        except KeyError:
            raise KeyError(
                "La rama '%s' no fue declarada. Llama a self.out.branch(...) "
                "en beginFile antes de llenarla." % name
            )
        if self._dtypes[name] in self._INT_DTYPES:
            buf[0] = int(value)
        else:
            buf[0] = float(value)


def _apply_branch_selection(tree, selection_file):
    """Aplica un archivo de seleccion de ramas estilo NanoAODTools:

        drop *
        keep nElectron
        keep MET_pt
        ...

    Reglas en orden: cada linea es "keep <patron>" o "drop <patron>", donde
    <patron> es una expresion regular (con "*" tratado como comodin ".*",
    ya que un "*" suelto no es una regex valida). La ultima regla que
    haga match sobre una rama define su estado. Las ramas contadoras y
    run/luminosityBlock/event quedan siempre activas.
    """
    all_branches = [b.GetName() for b in tree.GetListOfBranches()]
    if selection_file:
        status = {b: True for b in all_branches}
        with open(selection_file) as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                action, pattern = parts
                action = action.strip().lower()
                pattern = pattern.strip()
                if action not in ("keep", "drop"):
                    continue
                regex = re.compile("^" + pattern.replace("*", ".*") + "$")
                keep = action == "keep"
                for b in all_branches:
                    if regex.match(b):
                        status[b] = keep
    else:
        status = {b: True for b in all_branches}

    for b in all_branches:
        if b in _ALWAYS_ACTIVE or _COUNTER_RE.match(b):
            status[b] = True

    for b, keep in status.items():
        tree.SetBranchStatus(b, 1 if keep else 0)


def _load_json_lumi_mask(path):
    """Carga un JSON de luminosidad certificada (formato 'golden JSON' de
    CMS: {"<run>": [[lumi_ini, lumi_fin], ...], ...}) a un dict run -> rangos.
    """
    with open(path) as f:
        data = json.load(f)
    return {
        int(run): [(int(a), int(b)) for a, b in ranges] for run, ranges in data.items()
    }


def _passes_lumi_mask(mask, run, lumi):
    ranges = mask.get(run)
    if not ranges:
        return False
    return any(a <= lumi <= b for a, b in ranges)


class PostProcessor(object):
    def __init__(
        self,
        outputDir,
        inputFiles,
        cut=None,
        branchsel=None,
        modules=None,
        outputbranchsel=None,
        noOut=False,
        justcount=False,
        jsonInput=None,
        treeName="Events",
        outputTreeName=None,
        maxEntries=None,
        firstEntry=0,
        **_ignored_kwargs
    ):
        self.outputDir = outputDir
        self.inputFiles = list(inputFiles)
        self.cut = cut
        self.branchsel = branchsel
        self.outputbranchsel = outputbranchsel
        self.modules = list(modules) if modules else []
        self.noOut = noOut
        self.justcount = justcount
        self.treeName = treeName
        self.outputTreeName = outputTreeName or treeName
        self.maxEntries = maxEntries
        self.firstEntry = firstEntry
        self._lumi_mask = _load_json_lumi_mask(jsonInput) if jsonInput else None

    def run(self):
        if not self.noOut:
            os.makedirs(self.outputDir, exist_ok=True)

        for m in self.modules:
            m.beginJob()

        for path in self.inputFiles:
            self._process_file(path)

        for m in self.modules:
            m.endJob()

    def _process_file(self, path):
        fin = ROOT.TFile.Open(path)
        if not fin or fin.IsZombie():
            raise RuntimeError("No se pudo abrir el archivo de entrada: %s" % path)

        tin = fin.Get(self.treeName)
        if not tin:
            raise RuntimeError(
                "No se encontro el arbol '%s' en %s" % (self.treeName, path)
            )

        _apply_branch_selection(tin, self.branchsel)

        cut_formula = None
        if self.cut:
            cut_formula = ROOT.TTreeFormula("_mini_nanotools_cut", self.cut, tin)

        fout = None
        tout = None
        wrapped = None

        if not self.noOut:
            out_name = os.path.join(self.outputDir, os.path.basename(path))
            fout = ROOT.TFile.Open(out_name, "RECREATE")
            fout.cd()
            tout = tin.CloneTree(0)
            tout.SetName(self.outputTreeName)
            if self.outputbranchsel:
                _apply_branch_selection(tout, self.outputbranchsel)
            wrapped = WrappedOutputTree(tout)

        for m in self.modules:
            m.beginFile(fin, fout, tin, wrapped)

        n_total = tin.GetEntries()
        last = (
            n_total
            if self.maxEntries is None
            else min(n_total, self.firstEntry + self.maxEntries)
        )
        n_pass = 0

        for i in range(self.firstEntry, last):
            tin.GetEntry(i)

            if self._lumi_mask is not None:
                run = int(tin.GetLeaf("run").GetValue(0))
                lumi = int(tin.GetLeaf("luminosityBlock").GetValue(0))
                if not _passes_lumi_mask(self._lumi_mask, run, lumi):
                    continue

            if cut_formula is not None:
                cut_formula.GetNdata()
                if not cut_formula.EvalInstance():
                    continue

            event = Event(tin, i)
            keep = True
            for m in self.modules:
                if not m.analyze(event):
                    keep = False
                    break

            if keep:
                n_pass += 1
                if not self.noOut and not self.justcount:
                    tout.Fill()

        for m in self.modules:
            m.endFile(fin, fout, tin, wrapped)

        if not self.noOut:
            fout.cd()
            tout.Write()
            fout.Close()
            out_desc = os.path.join(self.outputDir, os.path.basename(path))
        else:
            out_desc = "(noOut=True, no se escribio archivo)"

        fin.Close()
        print(
            "[mini_nanotools] %s: %d/%d eventos pasaron -> %s"
            % (path, n_pass, n_total, out_desc)
        )
