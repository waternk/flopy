"""
mfbas module.  Contains the ModflowBas class. Note that the user can access
the ModflowBas class as `flopy.modflow.ModflowBas`.

Additional information for this MODFLOW package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/index.html?bas6.htm>`_.

"""

import sys
import numpy as np
from ..pakbase import Package
from ..utils import Util3d, check, get_neighbors

class ModflowBas(Package):
    """
    MODFLOW Basic Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.Modflow`) to which
        this package will be added.
    ibound : array of ints, optional
        The ibound array (the default is 1).
    strt : array of floats, optional
        An array of starting heads (the default is 1.0).
    ixsec : bool, optional
        Indication of whether model is cross sectional or not (the default is
        False).
    ichflg : bool, optional
        Flag indicating that flows between constant head cells should be
        calculated (the default is False).
    stoper : float
        percent discrepancy that is compared to the budget percent discrepancy
        continue when the solver convergence criteria are not met.  Execution
        will unless the budget percent discrepancy is greater than stoper
        (default is None). MODFLOW-2005 only
    hnoflo : float
        Head value assigned to inactive cells (default is -999.99).
    extension : str, optional
        File extension (default is 'bas'.
    unitnumber : int, optional
        FORTRAN unit number for this package (default is 13).

    Attributes
    ----------
    heading : str
        Text string written to top of package input file.
    options : list of str
        Can be either or a combination of XSECTION, CHTOCH or FREE.
    ifrefm : bool
        Indicates whether or not packages will be written as free format.

    Methods
    -------

    See Also
    --------

    Notes
    -----

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modflow.Modflow()
    >>> bas = flopy.modflow.ModflowBas(m)

    """
    def __init__(self, model, ibound=1, strt=1.0, ifrefm=True, ixsec=False,
                 ichflg=False, stoper=None, hnoflo=-999.99, extension='bas',
                 unitnumber=13):
        """
        Package constructor.

        """
        # Call ancestor's init to set self.parent, extension, name and unit
        # number
        Package.__init__(self, model, extension, 'BAS6', unitnumber)
        self.url = 'bas6.htm'
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        self.ibound = Util3d(model, (nlay, nrow, ncol), np.int, ibound,
                              name='ibound', locat=self.unit_number[0])
        self.strt = Util3d(model, (nlay, nrow, ncol), np.float32, strt,
                            name='strt', locat=self.unit_number[0])
        self.heading = '# Basic package file for MODFLOW, generated by Flopy.'
        self.options = ''
        self.ixsec = ixsec
        self.ichflg = ichflg
        self.stoper = stoper
        self.ifrefm = ifrefm
        #model.array_free_format = ifrefm
        model.free_format_input = ifrefm
        self.hnoflo = hnoflo
        self.parent.add_package(self)
        return

    def check(self, f=None, verbose=True, level=1):
        """
        Check package data for common errors.

        Parameters
        ----------
        f : str or file handle
            String defining file name or file handle for summary file
            of check method output. If a sting is passed a file handle
            is created. If f is None, check method does not write
            results to a summary file. (default is None)
        verbose : bool
            Boolean flag used to determine if check method results are
            written to the screen
        level : int
            Check method analysis level. If level=0, summary checks are
            performed. If level=1, full checks are performed.

        Returns
        -------
        None

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow.load('model.nam')
        >>> m.bas6.check()

        """
        chk = check(self, f=f, verbose=verbose, level=level)

        neighbors = get_neighbors(self.ibound.array)
        neighbors[np.isnan(neighbors)] = 0 # set neighbors at edges to 0 (inactive)
        chk.values(self.ibound.array,
                  (self.ibound.array > 0) & np.all(neighbors < 1, axis=0),
                   'isolated cells in ibound array', 'Warning')
        chk.values(self.ibound.array, np.isnan(self.ibound.array),
                   error_name='Not a number', error_type='Error')
        chk.summarize()
        return chk

    def write_file(self, check=True):
        """
        Write the package file.

        Parameters
        ----------
        check : boolean
            Check package data for common errors. (default True)

        Returns
        -------
        None

        """
        if check: # allows turning off package checks when writing files at model level
            self.check(f='{}.chk'.format(self.name[0]), verbose=self.parent.verbose, level=1)
        # Open file for writing
        f_bas = open(self.fn_path, 'w')
        # First line: heading
        #f_bas.write('%s\n' % self.heading)
        f_bas.write('{0:s}\n'.format(self.heading))
        # Second line: format specifier
        self.options = ''
        if self.ixsec:
            self.options += 'XSECTION'
        if self.ichflg:
            self.options += ' CHTOCH'
        if self.ifrefm:
            self.options += ' FREE'
        if self.stoper is not None:
            self.options += ' STOPERROR {0}'.format(self.stoper)
        f_bas.write('{0:s}\n'.format(self.options))
        # IBOUND array
        f_bas.write(self.ibound.get_file_entry())
        # Head in inactive cells
        f_bas.write('{0:15.6G}\n'.format(self.hnoflo))
        # Starting heads array
        f_bas.write(self.strt.get_file_entry())
        # Close file
        f_bas.close()

    @staticmethod
    def load(f, model, nlay=None, nrow=None, ncol=None, ext_unit_dict=None, check=True):
        """
        Load an existing package.

        Parameters
        ----------
        f : filename or file handle
            File to load.
        model : model object
            The model object (of type :class:`flopy.modflow.mf.Modflow`) to
            which this package will be added.
        nlay, nrow, ncol : int, optional
            If not provided, then the model must contain a discretization
            package with correct values for these parameters.
        ext_unit_dict : dictionary, optional
            If the arrays in the file are specified using EXTERNAL,
            or older style array control records, then `f` should be a file
            handle.  In this case ext_unit_dict is required, which can be
            constructed using the function
            :class:`flopy.utils.mfreadnam.parsenamefile`.
        check : boolean
            Check package data for common errors. (default True)
        Returns
        -------
        bas : ModflowBas object
            ModflowBas object (of type :class:`flopy.modflow.ModflowBas`)

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow()
        >>> bas = flopy.modflow.ModflowBas.load('test.bas', m, nlay=1, nrow=10,
        >>>                                      ncol=10)

        """

        if model.verbose:
            sys.stdout.write('loading bas6 package file...\n')

        if not hasattr(f, 'read'):
            filename = f
            f = open(filename, 'r')
        #dataset 0 -- header
        while True:
            line = f.readline()
            if line[0] != '#':
                break
        #dataset 1 -- options
        line = line.upper()
        opts = line.strip().split()
        ixsec = False
        ichflg = False
        ifrefm = False
        iprinttime = False
        ishowp = False
        istoperror = False
        stoper = None
        if 'XSECTION' in opts:
            ixsec = True
        if 'CHTOCH' in opts:
            ichflg = True
        if 'FREE' in opts:
            ifrefm = True
        if 'PRINTTIME' in opts:
            iprinttime = True
        if 'SHOWPROGRESS' in opts:
            ishowp = True
        if 'STOPERROR' in opts:
            istoperror = True
            i = opts.index('STOPERROR')
            stoper = np.float32(opts[i+1])
        #get nlay,nrow,ncol if not passed
        if nlay is None and nrow is None and ncol is None:
            nrow, ncol, nlay, nper = model.get_nrow_ncol_nlay_nper()
        #dataset 2 -- ibound
        ibound = Util3d.load(f, model, (nlay, nrow, ncol), np.int, 'ibound',
                              ext_unit_dict)
        #print ibound.array
        #dataset 3 -- hnoflo
        line = f.readline()
        hnoflo = np.float32(line.strip().split()[0])
        #dataset 4 -- strt
        strt = Util3d.load(f, model, (nlay, nrow, ncol), np.float32, 'strt',
                            ext_unit_dict)
        f.close()
        #create bas object and return
        bas = ModflowBas(model, ibound=ibound, strt=strt,
                         ixsec=ixsec, ifrefm=ifrefm, ichflg=ichflg,
                         stoper=stoper, hnoflo=hnoflo)
        if check:
            bas.check(f='{}.chk'.format(bas.name[0]), verbose=bas.parent.verbose, level=0)
        return bas
