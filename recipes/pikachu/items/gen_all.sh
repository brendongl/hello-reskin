#!/bin/bash
mkdir -p work/items/gen   # run from the repo root
# usage: gen_all.sh [names...]  (default: all)
names=${@:-$(python -c "import sys;sys.path.insert(0,'recipes/pikachu/items');import spec;print(' '.join(spec.JOBS))")}
gen1(){ n=$1; read -r ref subj < <(python -c "import sys;sys.path.insert(0,'recipes/pikachu/items');import spec;r,s=spec.JOBS['$n'];print(r, spec.STYLE.format(subj=s))")
  python tools/gen_image.py -o work/items/gen/$n.png -i "$(ls template/textures/*/$ref.png | head -1)" --aspect 1:1 "$subj" > work/items/gen/$n.log 2>&1 && echo "ok $n" || echo "FAIL $n $(tail -1 work/items/gen/$n.log)"; }
export -f gen1
printf '%s\n' $names | xargs -P 6 -I{} bash -c 'gen1 {}'
