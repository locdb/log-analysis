if (( $# != 1 )); then
    echo "Please provide log file as argument."
    exit -1
fi
mkdir -p tmp/
cp $1 tmp/$1.prep
vim tmp/$1.prep -c 'source prep.vim | write | quit'
python3 analyze.py < tmp/$1.prep
