if [[ $# != 1 ]]; then
    echo "Please provide log file as argument."
    exit -1
fi
mkdir -p tmp/
fname=$(basename $1)
cp $1 tmp/$fname.prep
vim tmp/$fname.prep -c 'source prep.vim | write | quit'
python3 analyze.py < tmp/$fname.prep
