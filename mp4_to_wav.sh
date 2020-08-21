input=$1
output=$2

mkdir -p $output

for f in $input/*.mp4
do
  echo "Converting ${f}..."
  filename=`basename ${f%%.*}`
  ffmpeg -i $f -ar 16000 -ac 1 -f wav $output/$filename.wav
done
