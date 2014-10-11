#!/usr/env/python
# coding: utf-8

# # Selecting Galaxies from SDSS

# We need about 10,000 galaxies from SDSS, in a narrow redshift range around
# z = 0.1, to match with our halos.

# We can grab this data from the <a
# href="http://skyserver.sdss3.org/public/en/tools/search/sql.aspx">SDSS
# skyserver SQL</a> server from python, using the `mechanize` web browser, and
# then manipulate the catalog with `pandas`.

# Querying skyserver, using code from Eduardo Martin's blog post at
# http://balbuceosastropy.blogspot.com/2013/10/an-easy-way-to-make-sql-queries-from.html

import numpy as np
from StringIO import StringIO  # To read a string like a file
import mechanize


def SDSS_select(sql):
    url = "http://skyserver.sdss3.org/dr10/en/tools/search/sql.aspx"
    br = mechanize.Browser()
    br.open(url)
    br.select_form(name="sql")
    br['cmd'] = sql
    br['format'] = ['csv']
    response = br.submit()
    file_like = StringIO(response.get_data())
    return file_like

# We want a sample of galaxies and their 5-band photometry, plus their
# redshifts and possibly positions.

ngal = 500000
galaxies = "SELECT top %i objid, ra, dec, dered_u, dered_g, \
dered_r, dered_i, dered_z, expRad_r FROM PhotoObj as p WHERE (type = 3) \
AND p.dered_i BETWEEN 0.0 AND 22.0"  % (ngal)

#galaxies = "SELECT top 500000 objid, ra, dec, z, dered_u AS mag_u,\
#dered_g AS mag_g, dered_r AS mag_r, dered_i AS mag_i,\
#dered_z AS mag_z FROM SpecPhoto as p WHERE (class = 'Galaxy')\
#AND (p.z BETWEEN 0.1 AND 0.2)"
print galaxies

# This SQL checks out at the [SkyServer SQL
# box](http://skyserver.sdss3.org/dr9/en/tools/search/sql.asp), which has
# a syntax checking option.
gal_file = SDSS_select(galaxies)
mytype = np.dtype([('id', 'int64'),
                   ('ra', 'float32'),
                   ('dec', 'float32'),
                   ('u', 'float32'),
                   ('g', 'float32'),
                   ('r', 'float32'),
                   ('i', 'float32'),
                   ('z', 'float32'),
                   ('radius', 'float32'),
                   ])
data = np.loadtxt(gal_file, dtype=mytype, delimiter=',', skiprows=2)
data.sort(order='i')
data = data[::-1]
print 'Originally pulled down %i halos' % data.size

mask = \
        (data['g'] < 22) * \
        (data['r'] < 22) * \
        (data['i'] < 22)
        #(data['u'] < 22) * \
        #* \
        #(data['z'] < 22)
cleaned = data[mask]

print 'Left with %i halos' % cleaned.size

header = """# SDF 1.0
parameter byteorder = 0x78563412;
# SDSS Galaxies
# %s
struct {
    int64_t id;
    float ra, dec;
    float u, g, r, i, z;
    float radius;
}[%i];
#\x0c
# SDF-EOH
""" % (galaxies, cleaned.size)

f = file("galaxies.sdf", "wb")
f.write(header)
cleaned.tofile(f)
f.close()
