import re

from morkdb import MorkDatabase
import morkast

def buildMork(astTree):
    '''
    Walk the abstract syntax tree and build a database from it.
    '''
    builder = _MorkBuilder(astTree)
    return builder.db

class _MorkBuilder(object):
    def __init__(self, astTree):
        self.astTree = astTree
        self.db = MorkDatabase()

        self.builders = {
            morkast.Dict  : self.buildDict,
            morkast.Table : self.buildTable,
            morkast.Row   : self.buildRow,
            morkast.Group : self.buildGroup,
        }

        self.build()

    def build(self):
        for item in self.astTree.items:
            builder = self.builders[item.__class__]
            builder(item)

    def inflateId(self, objid, defaultNamespace):
        namespace = objid.scope or defaultNamespace
        return self.db.dicts[namespace][objid.objcetid]

    def inflateCells(self, cells, columnNamespace='c', atomNamespace='a'):
        inflated = []
        for cell in cells:
            col = cell.column
            atom = cell.value
            if isinstance(col, morkast.ObjectRef):
                col = self.inflateId(col.obj, columnNamespace)

            if isinstance(atom, morkast.ObjectRef):
                atom = self.inflateId(atom.obj, atomNamespace)
            else:
                atom = self.unescape(atom)

            inflated.append((col, atom))

        return inflated

    _unescapeMap = {
        r'\)': ')', r'\\': '\\', r'\$': '$', # basic escapes
        '\\\r\n': '', '\\\n': '',            # line continuation
    }
    def translateEscape(self, match):
        text = match.group()
        if text.startswith('$'):
            return chr(int(text[1:], 16))

        return self._unescapeMap[text]

    _escape = re.compile(r'\$[0-9a-zA-Z]{2}|\\.|\\\r\n', re.DOTALL)
    def unescape(self, value):
        _escape.sub(self.translateEscape, value)

    def buildDict(self, astDict):
        # In this case, inflateCells should only be unescaping values.
        cells = dict(self.inflateCells(astDict.cells))

        # Find the namespace in the meta-dict, if any. Default is 'a'.
        namespace = 'a'
        assert len(astDict.meta) < 2, "Multiple meta-dicts? That's weird."
        if astDict.meta:
            meta = dict((cell.column, cell.value)
                for cell in astDict.meta[0].cells)
            # XXX Docs say this should be 'atomScope', but it seems to always be 'a'
            namespace = meta.get('a', 'a')

        d = self.db.dicts.setdefault(namespace, {})
        d.update(cells)

    def buildTable(self, astTable):
        pass

    def buildRow(self, astRow):
        pass

    def buildGroup(self, astGroup):
        pass

