regions="Brinstar Crateria Maridia Norfair Tourian Wrecked_Ship"
cd output
for i in $regions; do
    cd $i
    rm ./*
    cd ..
done
