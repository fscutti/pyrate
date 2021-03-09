

# this is not neccessary the smartest test but lets us figure out if the isntall worked

python3.8 -c "from pyrate.core.Job import Job"

if [ $? -ne 0 ];then
	echo "Install test failed."
	exit 1
else
	exit 0
fi

