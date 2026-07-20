class Module(object):
    """Clase base para modulos de analisis.

    Un modulo tipico solo necesita sobreescribir `beginFile` (para declarar
    las ramas de salida) y `analyze` (para llenarlas evento a evento).
    """

    def beginJob(self):
        """Llamado una vez, antes de procesar cualquier archivo."""
        pass

    def endJob(self):
        """Llamado una vez, despues de procesar todos los archivos."""
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        """Llamado al abrir cada archivo de entrada.

        Parameters
        ----------
        inputFile : ROOT.TFile
        outputFile : ROOT.TFile or None (si noOut=True)
        inputTree : ROOT.TTree
        wrappedOutputTree : mini_nanotools.postprocessor.WrappedOutputTree or None
        """
        pass

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        """Llamado al cerrar cada archivo de entrada, antes de escribirlo."""
        pass

    def analyze(self, event):
        """Llamado para cada evento.

        Debe devolver True si el evento pasa el filtro de este modulo
        (y por lo tanto debe seguir a los modulos siguientes / escribirse
        en el arbol de salida), o False para descartarlo.
        """
        return True
