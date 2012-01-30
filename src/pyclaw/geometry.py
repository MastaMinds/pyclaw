#!/usr/bin/env python
# encoding: utf-8
r"""
Module containing all Pyclaw solution objects
"""

import numpy as np

# ============================================================================
#  Default function definitions
# ============================================================================

# Default mapc2p function
def default_mapc2p(patch,x):
    r"""
    Returns the physical coordinate of the point x
    
    This is the stub function which simply returns the identity
    """
    return x


# ============================================================================
#  Dimension Object
# ============================================================================
class Dimension(object):
    r"""
    Basic class representing a dimension of a Patch object
    
    :Initialization:
    
    Input:
     - *name* - (string) string Name of dimension
     - *lower* - (float) Lower extent of dimension
     - *upper* - (float) Upper extent of dimension
     - *n* - (int) Number of cells
     - *units* - (string) Type of units, used for informational purposes only
       
    Output:
     - (:class:`Dimension`) - Initialized Dimension object

    Example:

    >>> x = Dimension('x',0.,1.,100)
    >>> print x
    Dimension x:  (n,d,[lower,upper]) = (100,0.01,[0.0,1.0])
    >>> x.name
    'x'
    >>> x.n
    100
    >>> x.d
    0.01
    >>> x.edge[0]
    0.0
    >>> x.edge[1]
    0.01
    >>> x.edge[-1]
    1.0
    >>> x.center[-1]
    0.995
    >>> len(x.center)
    100
    >>> len(x.edge)
    101
    """
    
    # ========== Property Definitions ========================================
    @property
    def ng(self):
        r"""(int) - Number of cells in this dimension, on this process"""
        return self.num_cells
    @property
    def delta(self):
        r"""(float) - Size of an individual, computational cell"""
        return (self.upper-self.lower) / float(self.num_cells)
    @property
    def edges(self):
        r"""(ndarrary(:)) - Location of all cell edge coordinates
        for this dimension"""
        if self._edges is None:
            self._edges = np.empty(self.num_cells+1)   
            for i in xrange(0,self.num_cells+1):
                self._edges[i] = self.lower + i*self.delta
        return self._edges
    _edges = None
    @property
    def centers(self):
        r"""(ndarrary(:)) - Location of all cell center coordinates
        for this dimension"""
        if self._centers is None:
            self._centers = np.empty(self.num_cells)
            for i in xrange(0,self.num_cells):
                self._centers[i] = self.lower + (i+0.5)*self.delta
        return self._centers
    _centers = None
    
    def __init__(self, *args, **kargs):
        r"""
        Creates a Dimension object
        
        See :class:`Dimension` for full documentation
        """
        
        # ========== Class Data Attributes ===================================
        self.name = 'x'
        r"""(string) Name of this coordinate dimension (e.g. 'x')"""
        self.num_cells = None
        r"""(int) - Number of cells in this dimension :attr:`units`"""
        self.lower = 0.0
        r"""(float) - Lower computational patch extent"""
        self.upper = 1.0
        r"""(float) - Upper computational patch extent"""
        self.units = None
        r"""(string) Corresponding physical units of this dimension (e.g. 
        'm/s'), ``default = None``"""
        
        # Parse args
        if isinstance(args[0],float):
            self.lower = float(args[0])
            self.upper = float(args[1])
            self.num_cells = int(args[2])
        elif isinstance(args[0],basestring):
            self.name = args[0]
            self.lower = float(args[1])
            self.upper = float(args[2])
            self.num_cells = int(args[3])
        else:
            raise Exception("Invalid initializer for Dimension.")
        
        for (k,v) in kargs.iteritems():
            setattr(self,k,v)

        #These aren't need for PyClaw, but we set them so that
        # the PyClaw patch has the same attributes as the PetClaw
        # patch, which allows for simpler programming elsewhere.
        self.nstart = 0
        self.nend = self.num_cells
        self.lowerg = self.lower
            
    def __str__(self):
        output = "Dimension %s" % self.name
        if self.units:
            output += " (%s)" % self.units
        output += ":  (num_cells,delta,[lower,upper]) = (%s,%s,[%s,%s])" \
            % (self.num_cells,self.delta,self.lower,self.upper)
        return output
        

# ============================================================================
#  Pyclaw Patch object definition
# ============================================================================
class Patch(object):
    r"""
    Basic representation of a single patch in Pyclaw
    
    :Dimension information:
    
        Each dimension has an associated name with it that can be accessed via
        that name such as ``patch.x.num_cells`` which would access the x dimension's
        number of cells.
    
    :Global Patch information:
    
        Each patch has a value for :attr:`level` and :attr:`patch_index`.
        
    :Properties:

        If the requested property has multiple values, a list will be returned
        with the corresponding property belonging to the dimensions in order.
         
    :Initialization:
    
        Input:
         - *dimensions* - (list of :class:`Dimension`) Dimensions that are to 
           be associated with this patch
            
        Output:
         - (:class:`Patch`) Initialized patch object

    A PyClaw Patch is usually constructed from a tuple of PyClaw Dimension objects:

        >>> x = Dimension('x',0.,1.,10)
        >>> y = Dimension('y',-1.,1.,25)
        >>> patch = Patch((x,y))
        >>> print patch
        Patch 1:
        Dimension x:  (num_cells,delta,[lower,upper]) = (10,0.1,[0.0,1.0])
        Dimension y:  (num_cells,delta,[lower,upper]) = (25,0.08,[-1.0,1.0])
        >>> patch.num_dim
        2
        >>> patch.num_cells
        [10, 25]
        >>> patch.lower
        [0.0, -1.0]
        >>> patch.delta
        [0.1, 0.08]

    A patch can be extended to higher dimensions using the add_dimension() method:

        >>> z=Dimension('z',-2.0,2.0,21)
        >>> patch.add_dimension(z)
        >>> patch.num_dim
        3
        >>> patch.num_cells
        [10, 25, 21]
        >>> patch.c_edges[0][0,0,0]
        0.0
        >>> patch.c_edges[1][0,0,0]
        -1.0
        >>> patch.c_edges[2][0,0,0]
        -2.0
    """

    # ========== Property Definitions ========================================
    @property
    def num_dim(self):
        r"""(int) - Number of dimensions"""
        return len(self._dimensions)
    @property
    def dimensions(self):
        r"""(list) - List of :class:`Dimension` objects defining the 
                patch's extent and resolution"""
        return [getattr(self,name) for name in self._dimensions]
    @property
    def num_cells(self): 
        r"""(list) - List of the number of cells in each dimension"""
        return self.get_dim_attribute('num_cells')
    @property
    def ng(self):
        r"""(list) - List of the local (to this process)number of cells in each dimension"""
        return self.get_dim_attribute('ng')
    @property
    def nstart(self):
        r"""(list) - List of the number of cells in each dimension"""
        return self.get_dim_attribute('nstart')
    @property
    def nend(self):
        r"""(list) - List of the number of cells in each dimension"""
        return self.get_dim_attribute('nend')
    @property
    def name(self):
        r"""(list) - List of names of each dimension"""
        return self._dimensions
    @property
    def lower(self):
        r"""(list) - Lower coordinate extents of each dimension"""
        return self.get_dim_attribute('lower')
    @property
    def lowerg(self):
        r"""(list) - Lower coordinate extents of each dimension on this process"""
        return self.get_dim_attribute('lowerg')
    @property
    def upper(self):
        r"""(list) - Upper coordinate extends of each dimension"""
        return self.get_dim_attribute('upper')
    @property
    def delta(self):
        r"""(list) - List of computational cell widths"""
        return self.get_dim_attribute('delta')
    @property
    def units(self):
        r"""(list) - List of dimension units"""
        return self.get_dim_attribute('units')
    @property
    def centers(self):
        r"""(list) - List of center coordinate arrays"""
        return self.get_dim_attribute('centers')
    @property
    def edges(self):
        "List of edge coordinate arrays"
        return self.get_dim_attribute('edges')
    @property
    def p_centers(self):
        r"""(list of ndarray(...)) - List containing the arrays locating
                  the physical locations of cell centers, see 
                  :meth:`compute_p_centers` for more info."""
        self.compute_p_centers(self)
        return self._p_centers
    _p_centers = None
    @property
    def p_edges(self):
        r"""(list of ndarray(...)) - List containing the arrays locating
                  the physical locations of cell edges, see 
                  :meth:`compute_p_edges` for more info."""
        self.compute_p_edges(self)
        return self._p_edges
    _p_edges = None
    @property
    def c_centers(self):
        r"""(list of ndarray(...)) - List containing the arrays locating
                  the computational locations of cell centers, see 
                  :meth:`compute_c_centers` for more info."""
        self.compute_c_centers(self)
        return self._c_centers
    _c_centers = None
    @property
    def c_edges(self):
        r"""(list of ndarray(...)) - List containing the arrays locating
                  the computational locations of cell edges, see 
                  :meth:`compute_c_edges` for more info."""
        self.compute_c_edges(self)
        return self._c_edges
    _c_edges = None

       
    
    # ========== Class Methods ===============================================
    def __init__(self,dimensions):
        r"""
        Instantiate a Patch object
        
        See :class:`Patch` for more info.
        """
        
        # ========== Attribute Definitions ===================================
        self.level = 1
        r"""(int) - AMR level this patch belongs to, ``default = 1``"""
        self.patch_index = 1
        r"""(int) - Patch number of current patch, ``default = 0``"""
        self.mapc2p = default_mapc2p
        r"""(func) - Patch mapping function"""
        self.gauges = []
        r"""(list) - List of gauges"""
        self.gauge_files     = []
        r"""(list) - List of files to write gauge values to"""
        self.gauge_path = './_output/_gauges/'
        r"""(string) - Full path to output directory for gauges"""
        # Dimension parsing
        if isinstance(dimensions,Dimension):
            dimensions = [dimensions]
        self._dimensions = []
        for dim in dimensions:
            self.add_dimension(dim)
    
    
    def __str__(self):
        output = "Patch %s:\n" % self.patch_index
        output += '\n'.join((str(getattr(self,dim)) for dim in self._dimensions))
        return output
    
    
    # ========== Dimension Manipulation ======================================
    def add_dimension(self,dimension):
        r"""
        Add the specified dimension to this patch
        
        :Input:
         - *dimension* - (:class:`Dimension`) Dimension to be added
        """

        # Add dimension to name list and as an attribute
        self._dimensions.append(dimension.name)
        setattr(self,dimension.name,dimension)
        
        
    def get_dim_attribute(self,attr):
        r"""
        Returns a tuple of all dimensions' attribute attr
        """
        return [getattr(getattr(self,name),attr) for name in self._dimensions]
    
    
    # ========== Copy functionality ==========================================
    def __copy__(self):
        return self.__class__(self)
        
        
    def __deepcopy__(self,memo={}):
        import copy
        result = self.__class__(copy.deepcopy(self.dimensions))
        result.__init__(copy.deepcopy(self.dimensions))
        
        for attr in ('level','patch_index','_p_centers','_p_edges',
                        '_c_centers','_c_edges'):
            setattr(result,attr,copy.deepcopy(getattr(self,attr)))
        
        result.mapc2p = self.mapc2p
        
        return result
        
    
    # ========== Patch Operations =============================================
    def compute_p_centers(self, recompute=False):
        r"""Calculates the :attr:`p_centers` array, which contains the physical
        coordinates of the cell centers when a mapping is used.

        patch._p_centers is a list of numpy arrays.  Each array has shape equal
        to the shape of the patch; the number of arrays is equal to the 
        dimension of the embedding space for the mapping.
        
        This array is computed only when requested and then stored for later 
        use unless the recompute flag is set to True (you may want to do this
        for time-dependent mappings).
        
        Access the resulting physical coordinate array via the corresponding
        dimensions or via the computational patch properties :attr:`p_centers`.
        
        :Input:
         - *recompute* - (bool) Whether to force a recompute of the arrays
        """
        
        if recompute or not len(self._p_centers) == len(self._dimensions):
            # Initialize array
            self._p_centers = [None]*self.num_dim

            # Special case
            if self.num_dim == 1:
                self._p_centers[0] = self.mapc2p(self,self.dimensions[0].centers)
            # Higer dimensional calculate center arrays
            else:
                index = np.indices(self.ng)
                array_list = []
                for i,center_array in enumerate(self.get_dim_attribute('centers')):
                    #We could just use indices directly and deal with
                    #numpy arrays instead of lists of numpy arrays
                    array_list.append(center_array[index[i,...]])
            
                self._p_centers = self.mapc2p(self,array_list)
 

    def compute_p_edges(self, recompute=False):
        r"""Calculates the :attr:`p_edges` array
        
        This array is computed only when requested and then stored for later 
        use unless the recompute flag is set to True (you may want to do this
        for time dependent mappings).
        
        Access the resulting physical coordinate array via the corresponding
        dimensions or via the computational patch properties :attr:`p_edges`.
        
        :Input:
         - *recompute* - (bool) Whether to force a recompute of the arrays
        """
        
        if recompute or not len(self._p_edges) == len(self._dimensions):
            # Initialize array
            self._p_edges = [None for i in xrange(self.num_dim)]

            if self.num_dim == 1:        
                self._p_edges[0] = self.mapc2p(self,self.dimensions[0].edges)
            else:
                index = np.indices([n+1 for n in self.ng])
                array_list = []
                for i,edge_array in enumerate(self.get_dim_attribute('edges')):
                    #We could just use indices directly and deal with
                    #numpy arrays instead of lists of numpy arrays
                    array_list.append(edge_array[index[i,...]])
            
                self._p_edges = self.mapc2p(self,array_list)
            

    def compute_c_centers(self, recompute=False):
        r"""
        Calculate the :attr:`c_centers` array
        
        This array is computed only when requested and then stored for later
        use unless the recompute flag is set to True.
        
        Access the resulting computational coodinate array via the
        corresponding dimensions or via the computational patch properties
        :attr:`c_centers`.
        
        :Input:
         - *recompute* - (bool) Whether to force a recompute of the arrays
        """
        
        if recompute or (self._c_centers is None):
            self._c_centers = [None]*self.num_dim
            
            # For one dimension, the center and edge arrays are equivalent
            if self.num_dim == 1:
                self._c_centers[0] = self.dimensions[0].centers
            else:
                index = np.indices(self.ng)
                self._c_centers = []
                for i,center_array in enumerate(self.get_dim_attribute('centers')):
                    #We could just use indices directly and deal with
                    #numpy arrays instead of lists of numpy arrays
                    self._c_centers.append(center_array[index[i,...]])

    def compute_c_edges(self, recompute=False):
        r"""
        Calculate the :attr:`c_edges` array
        
        This array is computed only when requested and then stored for later
        use unless the recompute flag is set to True.
        
        Access the resulting computational coodinate array via the
        corresponding dimensions or via the computational patch properties
        :attr:`c_edges`.
        
        :Input:
         - *recompute* - (bool) Whether to force a recompute of the arrays
        """
        if recompute or not len(self._c_edges) == len(self._dimensions):
            self._c_edges = [None for i in xrange(self.num_dim)]
            
            if self.num_dim == 1:
                self._c_edges[0] = self.dimensions[0].edges
            else:
                index = np.indices([n+1 for n in self.ng])
                self._c_edges = []
                for i,edge_array in enumerate(self.get_dim_attribute('edges')):
                    #We could just use indices directly and deal with
                    #numpy arrays instead of lists of numpy arrays
                    self._c_edges.append(edge_array[index[i,...]])
            

    # ========================================================================
    #  Gauges
    # ========================================================================
    def add_gauges(self,gauge_coords):
        r"""
        Determine the cell indices of each gauge and make a list of all gauges
        with their cell indices.  
        
        For PetClaw, first check whether each gauge is in the part of the patch
        corresponding to this patch.

        THIS SHOULD BE MOVED TO GRID
        """
        import os
        from numpy import floor
        if not os.path.exists(self.gauge_path):
            try:
                os.makedirs(self.gauge_path)
            except OSError:
                print "gauge directory already exists, ignoring"
        
        for gauge in gauge_coords: 
            # Determine gauge locations in units of mesh spacing
            gauge_ind = [int(floor(gauge[n]/self.delta[n])) for n in xrange(self.num_dim)]
            if all(self.nstart[n]<=gauge_ind[n]<self.nend[n] for n in range(self.num_dim)):
                #Set indices relative to this patch
                gauge_ind = [gauge_ind[n] - self.nstart[n] for n in range(self.num_dim)]
                gauge_path = self.gauge_path+'gauge'+'_'.join(str(coord) for coord in gauge)+'.txt'
                # Is this a good idea???  It should depend on self.overwrite.
                if os.path.isfile(gauge_path): 
                    os.remove(gauge_path)
                self.gauges.append(list(gauge_ind))
                self.gauge_files.append(open(gauge_path,'a'))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
