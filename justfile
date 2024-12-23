
# define GRF name here
GRF := "wuse"

def: preprocess build
    @echo "Finished building"

preprocess:
    python3 src/roadtypes.py
    gcc -E -x c {{GRF}}.pnml > {{GRF}}.nml

build:
    nml/nmlc -c --list-unused-strings {{GRF}}.nml --nml={{GRF}}_parsed.nml --grf={{GRF}}.grf
    md5sum {{GRF}}.grf >> build.log
    date +'%Y%m%d%H%M%S' >> build.log

test:
    nml/nmlc -c --list-unused-strings {{GRF}}_parsed.nml --grf={{GRF}}.grf
    md5sum {{GRF}}.grf >> build.log
    date +'%Y%m%d%H%M%S' >> build.log

clean:
    # remove all .nml and .grf files
    find . -type f -name '*.nml' -delete
    find . -type f -name '*.grf' -delete

cp:
    cp {{GRF}}.grf ~/.local/share/openttd/newgrf/
