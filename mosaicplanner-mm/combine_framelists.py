import os

root = "/Users/SJSmith/Documents/Nick Local/data/ISI-Barrels/Ct1-ISI/R55/Imaging-Sessions"

cols = ['C3', 'C2', 'C1']
nframes = 3
flist_names = []
flist_paths = []
flists = []
for col in cols:
    flist_name_tmp = "2012-05-07_Ct1-R55_session1_%sL4_posList-1x3frames.csv" %col
    flist_names.append(flist_name_tmp)
    flist_paths.append(os.path.join(root, flist_name_tmp))

for path in flist_paths:
    with open(path, 'r') as f:
        flists.append(f.readlines())
    assert f.closed == True

newpath = os.path.join(root, "2012-05-07_Ct1-R55_session1_combined-posList-1x3frames.csv")

with open(newpath, 'w') as f:
    # write header lines from first input file
    for line in range(7):
        f.write(flists[0][line])
    # interleave lines from input files into output file
    assert (len(flists[0])-7)%nframes == 0
    # for each section
    for secnum in range((len(flists[0])-7)/nframes):
        print "secnum %d" %secnum
        # for each column in the section
        for colnum in range(len(cols)):
            print "colnum %d" %colnum
            # for each frame in the column
            for fnum in range(nframes):
                print "fnum %d" %fnum
                line = 7+(secnum*nframes)+fnum
                print "line %d" %line
                f.write('"%s_%s' %(cols[colnum],flists[colnum][line][1::]))
                print '"%s_%s' %(cols[colnum],flists[colnum][line][1::])
assert f.closed == True
