
from . import base
from . import curseforge
from . import modrinth

__all__ = []

def export_pkg(pkg):
	if hasattr(pkg, '__all__'):
		globals()['__all__'].extend(pkg.__all__)
		for n in pkg.__all__:
			globals()[n] = getattr(pkg, n)

export_pkg(base)
export_pkg(curseforge)
export_pkg(modrinth)
