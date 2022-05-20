python3 -c "import ROOT"
if [ $? -ne 0 ];then
	echo "CHECK for ROOT failed."
	exit 1
else
	exit 0
fi


