## (0) Prepare data directory
rootdir="/media/pi/data/"
fle="PMoutputData"
i="0"

#Try 100 times and then stop
while [ $i -lt 100 ]; do

	i=$[$i+1];
	fle2find="${rootdir}${fle}${i}"

	if [ ! -d $fle2find ]; then

		sudo cp -r "/media/pi/data/PMoutputData" $fle2find;
		sudo rm -r /media/pi/data/PMoutputData/*;
		break;

	fi

	if [ $i -eq 99 ]; then 
		touch '/home/pi/Desktop/DirectoryProblem.txt'; 
		echo "Data Backup File N > 99: Check /media/pi/data/PMoutputData/" >  '/home/pi/Desktop/DirectoryProblem.txt';
	fi

done

