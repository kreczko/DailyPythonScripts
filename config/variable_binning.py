
eta_bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]

bin_edges = {
             'MET':[0.0, 31.0, 58.0, 96.0, 142.0, 191.0, 300],
             'HT':[0.0, 190.0, 225.0, 262.0, 302.0, 345.0, 392.0, 445.0, 501.0, 562.0, 623.0, 689.0, 766.0, 1000],
             'ST':[0.0, 285.0, 329.0, 376.0, 428.0, 484.0, 544.0, 609.0, 678.0, 751.0, 830.0, 911.0, 1028.0, 1200],
             'MT':[0.0, 28.0, 66.0, 100],
             'WPT':[0.0, 31.0, 59.0, 88.0, 118.0, 151.0, 187.0, 227.0, 267.0, 300]
             }

# should we want separate binning for different centre of mass energies
# we can put the logic here, maybe as a function:
# get_variable_binning(centre_of_mass_energy, combined = False)
# where combined gives you the best bins across the different
# centre of mass energies

bin_widths = {}
variable_bins_ROOT = {}
variable_bins_latex = {}
# calculate all the other variables
for variable in bin_edges.keys():
    bin_widths[variable] = []
    variable_bins_ROOT[variable] = []
    number_of_edges = len( bin_edges[variable] )
    for i in range( number_of_edges - 1 ):
        lower_edge = bin_edges[variable][i]
        upper_edge = bin_edges[variable][i + 1]
        bin_widths[variable].append( upper_edge - lower_edge )
        bin_name = '%d-%d' % ( int( lower_edge ), int( upper_edge ) )
        bin_name_latex = '%d--%d~\GeV' % ( int( lower_edge ), int( upper_edge ) )
        if ( i + 1 ) == number_of_edges - 1:
            bin_name = '%d-inf' % int( lower_edge )
            bin_name_latex = '$\\geq %d$~\GeV' % int( lower_edge )
        variable_bins_ROOT[variable].append( bin_name )
        variable_bins_latex[bin_name] = bin_name_latex