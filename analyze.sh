mkdir -p tmp/
cp $1 tmp/$1.prep
vim tmp/$1.prep -c 'source prep.vim | write | quit'
python3 analyze.py tmp/$1.prep
