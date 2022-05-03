run/rando.smc: run/sm_JU.smc settings/items.set settings/seed settings/starting
	python door_rando_main.py --settings settings\
		--clean $< --create $@\
		--seed `cat settings/seed` --completable\
		--starting_items `cat settings/starting`\
		--noescape
