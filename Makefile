run:
	mkdir $@

run/sm_JU.smc: run
	echo "You'll need to put your Super Metroid Japanese Unheadered ROM file into the run directory and name it 'sm_JU.smc'."

run/rando.smc: run/sm_JU.smc run settings/items.set settings/seed settings/starting
	python door_rando_main.py --settings settings\
		--clean $< --create $@\
		--seed `cat settings/seed` --completable\
		--starting_items `cat settings/starting`\
		--noescape
