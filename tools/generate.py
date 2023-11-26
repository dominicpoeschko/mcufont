import sys
import subprocess
import tempfile
import shutil
import glob

fontfile = sys.argv[2]
outfile = sys.argv[3]
size = sys.argv[4]
iterations = sys.argv[5]
bw_font = sys.argv[6]

tmpdir = tempfile.mkdtemp()

subprocess.check_output(
    [sys.argv[1],
    "import_ttf",
    fontfile,
    size,
    "bw"],
    cwd=tmpdir
)

datafile = glob.glob(tmpdir+"/*.dat")[0]

args = [sys.argv[1], "filter", datafile]
args.extend(sys.argv[7:])
subprocess.check_output(
    args,
    cwd=tmpdir
)

if bw_font == "0":
    args = [sys.argv[1], "rlefont_optimize", datafile, iterations]

    p = subprocess.Popen(
        args,
        cwd=tmpdir
    )

    p.wait()

    args = [sys.argv[1], "rlefont_size", datafile]

    p = subprocess.Popen(
        args,
        cwd=tmpdir
    )

    p.wait()

    args = [sys.argv[1], "rlefont_export", datafile, outfile]
else:
    args = [sys.argv[1], "bwfont_export", datafile, outfile]

subprocess.check_output(
    args,
    cwd=tmpdir
)

shutil.rmtree(tmpdir)

