import re

_COUNTER_RE = re.compile(r"^n[A-Z]")


class Event(object):
    """Envuelve una entrada (evento) ya cargada de un TTree de entrada.

    Permite `event.MET_pt`, `event.HLT_Mu50`, etc. igual que en
    PhysicsTools.NanoAODTools.
    """

    def __init__(self, tree, entry):
        # Evitar pasar por __setattr__/__getattr__ personalizados para estos:
        object.__setattr__(self, "_tree", tree)
        object.__setattr__(self, "_entry", entry)
        object.__setattr__(self, "_cache", {})

    def _read_branch(self, name):
        cache = self._cache
        if name in cache:
            return cache[name]

        leaf = self._tree.GetLeaf(name)
        if not leaf:
            raise AttributeError(
                "Rama '%s' no encontrada. Revisa el nombre de la rama." % name
            )

        if self._tree.GetBranchStatus(name) == 0:
            raise AttributeError(
                "Rama '%s' esta desactivada (branchsel hizo drop de ella). "
                "Si tu modulo necesita leerla, reactivala con "
                "inputTree.SetBranchStatus('%s', 1) en beginFile." % (name, name)
            )

        n = leaf.GetNdata()
        if n <= 1:
            value = leaf.GetValue(0)
        else:
            value = [leaf.GetValue(i) for i in range(n)]

        cache[name] = value
        return value

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._read_branch(name)

    def _get_scalar(self, name):
        value = self._read_branch(name)
        if isinstance(value, list):
            raise ValueError("Se esperaba una rama escalar para '%s'" % name)
        return int(value)

    def _get_collection_value(self, prefix, field, index):
        branch_name = "%s_%s" % (prefix, field)
        values = self._read_branch(branch_name)
        if not isinstance(values, list):
            # Rama de largo 1 (poco comun, pero valido)
            return values
        return values[index]


class Object(object):
    """Un elemento de una Collection (p.ej. un Electron o un Muon)."""

    def __init__(self, event, prefix, index):
        object.__setattr__(self, "_event", event)
        object.__setattr__(self, "_prefix", prefix)
        object.__setattr__(self, "_index", index)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._event._get_collection_value(self._prefix, name, self._index)

    def __repr__(self):
        return "<%s[%d]>" % (self._prefix, self._index)


class Collection(object):
    """Reconstruye una coleccion NanoAOD ("Electron", "Muon", ...) a partir
    de su rama contadora ("nElectron", "nMuon", ...) y sus ramas "Prefijo_campo".
    """

    def __init__(self, event, prefix, sizename=None):
        self._event = event
        self._prefix = prefix
        self._sizename = sizename or ("n" + prefix)
        self._n = event._get_scalar(self._sizename)

    def __len__(self):
        return self._n

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [
                Object(self._event, self._prefix, i)
                for i in range(*index.indices(self._n))
            ]
        if index < 0:
            index += self._n
        if not (0 <= index < self._n):
            raise IndexError("indice %d fuera de rango (n=%d)" % (index, self._n))
        return Object(self._event, self._prefix, index)

    def __iter__(self):
        for i in range(self._n):
            yield Object(self._event, self._prefix, i)

    def __repr__(self):
        return "<Collection %s n=%d>" % (self._prefix, self._n)
