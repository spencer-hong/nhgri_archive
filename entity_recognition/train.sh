#!/bin/bash

# Define the number of folders to create
TRAIN_SAMPLE_SIZES=("100" "200" "300" "400" "500")


# Define the name of the training script to run
TRAIN_SCRIPT="python -m spacy train train.cfg"
# Loop over the number of folders to create
for sample in "${TRAIN_SAMPLE_SIZES[@]}"
do
	for ((j=0; j<=10; j++))
	do
	# Create a new folder for this iteration
	OUTPUT_FOLDER="data_curve/${sample}_samples/runs_${j}/"
	TRAIN_FILE="data_curve/${sample}_samples/train_${j}.spacy"
	DEV_FILE="data_curve/holdout_${j}.spacy"

	#SOURCE_FOLDER="manuscript/from_just_training_examples/runs_v4/model-best/"

	echo "Currently on Sample ${sample}, Run ${j}"

	#$TRAIN_SCRIPT --paths.train $TRAIN_FILE --paths.dev $DEV_FILE --gpu-id 0 --paths.source $SOURCE_FOLDER --output $OUTPUT_FOLDER
	
	# Start training using the specified script
	$TRAIN_SCRIPT --paths.train $TRAIN_FILE --paths.dev $DEV_FILE --gpu-id 0 --output $OUTPUT_FOLDER

	done
done
