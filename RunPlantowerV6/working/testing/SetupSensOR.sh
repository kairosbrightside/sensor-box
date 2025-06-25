#! /bin/bash


rootdir="/media/pi/data/"
fle="PMoutputData"
i="0"

while true; do

	i=$[$i+1];
	fle2find="${rootdir}${fle}${i}"

	if [ ! -d $fle2find ]; then

		sudo cp -r "/media/pi/data/PMoutputData" $fle2find;
		sudo rm -r /media/pi/data/PMoutputData/*;
		break;
	fi

done