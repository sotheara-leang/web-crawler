input=$1
output=$2

mkdir -p $output

for f in $input/*.mp3
do
  echo "Converting ${f}..."
  filename=`basename $f .mp3`
  sox $f -c 1 -r 16000 $output/$filename.wav
done