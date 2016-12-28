# Represents the object file recognized by the Luz architecture.
# An object file is relocatable. It is created by the assembler,
# and later combined with other object files by the linker into
# an executable.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

class ObjectFile(object):
    """ Use one of the factory methods to create ObjectFile
        instances: from_assembler, from_file

        The name of the object can be accessed via the .name
        attribute.
    """
    def __init__(self):
        self.seg_data = {}
        self.export_table = []
        self.import_table = []
        self.reloc_table = []

        self.name = None

    @classmethod
    def from_assembler( cls,
                        seg_data,
                        export_table,
                        import_table,
                        reloc_table):
        """ Create a new ObjectFile from assembler-generated data
            structures.
        """
        obj = cls()
        assert isinstance(seg_data, dict)
        for table in (export_table, import_table, reloc_table):
            assert isinstance(table, list)

        obj.seg_data = seg_data
        obj.export_table = export_table
        obj.import_table = import_table
        obj.reloc_table = reloc_table
        return obj

    @classmethod
    def from_file(cls, file):
        """ 'file' is either a filename (a String), or a readable
            IO object.
        """
        pass
