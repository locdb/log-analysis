if [[ $# != 1 ]]; then
    echo "Please provide log file as argument."
    exit -1
fi
mkdir -p prep/
fname=$(basename $1)
cp $1 prep/$fname.prep
vim prep/$fname.prep -c 'source prep.vim | write | quit'
python3 analyze.py < prep/$fname.prep
