#!/bin/bash

# parameters

start=$(date -u +"%s")

WD=$(pwd)
scriptPath='/home/tamp/pep.lib/proc/'
#scriptPath='/home/papst/VMANIP/technical/software/'

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$scriptPath/../bin
 
# function

#usage(){
#	echo ""
#	echo "Usage : $0 INPUT_DIR OUTPUT_DIR"
#    echo ""
#}

#FOLDER_INPUT=$1
#FOLDER_OUTPUT=$2

TYPE=$1

FOLDER_OUTPUT='/das-dave_data/inBasket/'

#if [ ! -d "$FOLDER_INPUT" ]; then
#        echo -e "\nInput Folder doesn't exist"
#        usage
#        exit 1
#fi

#if [ ! -d "$FOLDER_OUTPUT" ]; then
#        echo -e "\nOutput Folder doesn't exist"
#        usage
#        exit 1
#fi

procFLEXPART()
{
	echo ""
	echo "--------------------------------------------------"
	echo "Processing FLEXPART"
	FOLDER_INPUT='/das-dave_data/inData/HOLU_SO2_35kt_FLEXPART'
	cd $FOLDER_OUTPUT
	mkdir -p FLEXPART
	cd FLEXPART
	python $scriptPath/procFLEXPART.py $FOLDER_INPUT
}

procAURA_L2()
{
	echo ""
	echo "--------------------------------------------------"
	echo "Processing AURA level 2"
	FOLDER_INPUT='/das-dave_data/inData/AURA_L2'
	HDF=($(find $FOLDER_INPUT -name OMI.L2*.he5))
	cd $FOLDER_OUTPUT
	mkdir -p AURA_L2
	cd AURA_L2
	for img in ${HDF[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procAURA_L2.py  $img
	done
}

procAURA_L3()
{
	echo ""
	echo "--------------------------------------------------"
	echo "Processing AURA level 3"
	FOLDER_INPUT='/das-dave_data/inData/AURA_L3'
	HDF=($(find $FOLDER_INPUT -name OMI-Aura_L3*.he5))
	cd $FOLDER_OUTPUT
	mkdir -p AURA_L3
	cd AURA_L3
	for img in ${HDF[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procAURA_L3.py  $img
	done
}

procWRFCHEM()
{
	echo ""
	echo "--------------------------------------------------"
	echo "Processing WRF-CHEM"
	FOLDER_INPUT='/das-dave_data/inData/HOLU_SO2_WRFCHEM'
	GRIB=($(find $FOLDER_INPUT -name wrfout_*))
	cd $FOLDER_OUTPUT
	mkdir -p WRF-CHEM
	cd WRF-CHEM
	for img in ${GRIB[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procWRFCHEM.py  $img
	done
}

procALARO()
{
	echo ""
	echo "--------------------------------------------------"
	echo "Processing ALARO"
	FOLDER_INPUT='/das-dave_data/inData/ALARO'
	GRIB=($(find $FOLDER_INPUT -name ALARO*.grb))
	cd $FOLDER_OUTPUT
	mkdir -p ALARO
	cd ALARO
	for img in ${GRIB[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procALARO.py  $img
	done
}

procAROME()
{
	echo ""
	echo "--------------------------------------------------"
	echo "AROME"
	FOLDER_INPUT='/das-dave_data/inData/AROME'
	GRIB=($(find $FOLDER_INPUT -name AROME*.grb))
	cd $FOLDER_OUTPUT
	mkdir -p AROME
	cd AROME
	for img in ${GRIB[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procAROME.py  $img
	done
}

procCloudsat()
{
	echo ""
	echo "--------------------------------------------------"
	echo "CLOUDSAT"
	FOLDER_INPUT='/das-dave_data/inData/CLOUDSAT'
	HDF=($(find $FOLDER_INPUT -name *.hdf))
	cd $FOLDER_OUTPUT
	mkdir -p CLOUDSAT
	cd CLOUDSAT
	for img in ${HDF[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procCloudsat.py  $img
	done
}

procMOD07()
{
	echo "--------------------------------------------------"
	echo "Processing MOD07"
	FOLDER_INPUT='/das-dave_data/inData/MOD07_15.05.2013'
	HDF=($(find $FOLDER_INPUT  -name MOD07_L2*.hdf))
	cd $FOLDER_OUTPUT
	mkdir -p MOD07
	cd MOD07
	for img in ${HDF[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procMODL2_MOD07.py  $img
	done
}

procMYD07()
{
	echo "--------------------------------------------------"
	echo "Processing MYD07"
	FOLDER_INPUT='/das-dave_data/inData/MOD07_15.05.2013'
	HDF=($(find $FOLDER_INPUT  -name MYD07_L2*.hdf))
	cd $FOLDER_OUTPUT
	for img in ${HDF[@]}
	do
	  echo "Processing  $img ... "
	  python $scriptPath/procMODL2_MOD07.py  $img
	done
}

case "$TYPE" in
	WRF-CHEM) procWRFCHEM
		;;
	
	ALARO) procALARO
		;;

	AROME) procAROME
		;;

	Cloudsat) procCloudsat
		;;

	MOD07) procMOD07
		;;

	AURA_L2) procAURA_L2
		;;

	AURA_L3) procAURA_L3
		;;

	FLEXPART) procFLEXPART
		;;

	all) procWRFCHEM;
			 procALARO;
			 procAROME;
			 procCloudsat;
			 procMOD07;
			 procAURA_L2;
			 procAURA_L3;
			end=$(date -u +"%s")
			diff=$(($end-$start))
			echo "$(($diff / 60))m and $(($diff % 60))s elapsed"
		;;
esac
