
i=0
for v in $@;do
	case $i in
		0)
			echo "task number:$v\n"
			tasks=$v
			;;
		*)
			echo "unsupported arg: $v"
	esac	
	let ++i
done
echo $tasks

i=0
while (( $i<$tasks)); do
	( echo 'start new task '$i; python3 ./test.py )&
	let ++i
done
wait
