#!/bin/bash
cd /home/osf/SearchAndRescueTool
echo "Running VERSION2" >> hullsegment_$1.log
ProbabilitiesJsonFile="$1.json";
Area_Pro="area_$1.dat";
Dat="final_$1.dat";
Hull_Seg="finalconvexhull_$1.dat";
GmtReg="gmtregion_$1.txt";
UniqId=$1
#rm ${GmtReg} proval-*-interval5-*.xy
rm ${GmtReg} proval-*.xy

awk '{printf "%d %.3f\n", $1,$2}' $Area_Pro >$Dat
ProVal=( $( awk '{printf "%.3f\n", $2}' $Dat |  sort | uniq | paste -s ) )
#gt=(    0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 )
# gt=( 0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 )
gt=( 0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.6 0.7 0.8 0.9 )

#lt=( 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0 )
# lt=( 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1.0 )
lt=( 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.6 0.7 0.8 0.9 1.0 )

lkp_lat=$(head -1 ${Hull_Seg} | awk '{print $2}')
lkp_lon=$(head -1 ${Hull_Seg} | awk '{print $1}')

echo "{" >${ProbabilitiesJsonFile}
echo "\"type\":\"FeatureCollection\"," >>${ProbabilitiesJsonFile}
echo "\"features\":[" >>$ProbabilitiesJsonFile


# echo "{\"type\":\"feature\"" >>${ProbabilitiesJsonFile}
# echo "\"geometry\": {" >>$ProbabilitiesJsonFile
# echo "\"type\":\"Point\"," >>$ProbabilitiesJsonFile
# echo "\"coordinates\":[${lkp_lon}, ${lkp_lat}]" >>${ProbabilitiesJsonFile}
# echo "}," >>$ProbabilitiesJsonFile
# echo "\"properties\":{\"name\":\"LKP\"}" >> ${ProbabilitiesJsonFile}
# echo "}," >>$ProbabilitiesJsonFile

##
function get_lines(){
   i=$1;conf=$2;comma=$3;pro_val="$4"
 		for line in $(grep  "${ProVal[$i]}" $Dat | awk '{print $1}' | paste -s);do
			# echo ${line}
                                        x=$(( $line * 3 - 2 ));y=$(( $line * 3 + 1 ))
                                        echo "** ${ProVal[$i]} -- >> $line $x:$y **"
					# awk 'NR >='$x' && NR <='$y' {print $1,$2} ' $Hull_Seg 
					echo $pro_val >>$GmtReg
                    # awk 'NR >='$x' && NR <='$y' {print $1,$2} ' $Hull_Seg  >>proval-${pro_val}-interval5-${UniqId}.xy
					awk 'NR >='$x' && NR <='$y' {print $1,$2} ' $Hull_Seg  >>proval-${pro_val}-${UniqId}.xy
					
					echo "{\"type\":\"Feature\"," >>${ProbabilitiesJsonFile}
					echo "\"geometry\": {" >>${ProbabilitiesJsonFile}
					echo "\"type\":\"MultiPolygon\"," >>${ProbabilitiesJsonFile}
                    echo "\"coordinates\":[[[" >>${ProbabilitiesJsonFile}
					# Dynamically truncate coordinates up to 6 decimal places
					echo "`awk 'NR >='$x' && NR <='$y' {x=index($1,"."); x=(x?x+6:length($1)); y=index($2,"."); y=(y?y+6:length($2)); print "["substr($1,1,x)","substr($2,1,y)"],"} ' $Hull_Seg | sed '$ s/,$//g'`" >>${ProbabilitiesJsonFile}
                    echo " ]]]},">>${ProbabilitiesJsonFile}
					echo "\"properties\":{\"confidence\":$pro_val,\"time\":1430391800.0000000}" >>$ProbabilitiesJsonFile
					echo "}," >>${ProbabilitiesJsonFile}
        done
}
##
	for (( i=0;i<${#ProVal[@]};i++  ));do
		#if [[  `echo "${ProVal[$i]} > 0 " | bc -l` != 0 ]];then
			# for (( j=0;j<10;j++ ));do			
			# for (( j=0;j<20;j++ ));do
			for (( j=0; j<15; j++ )); do
				if [[ `echo " ${ProVal[$i]} >= ${gt[$j]} && ${ProVal[$i]} <= ${lt[$j]} " | bc -l` != 0  ]];then
					# echo "${ProVal[$i]}, ${j}, ${lt[$j]}"
					#echo " > ${gt[$j]} && <= ${lt[$j]} + ${lt[$j]} + $j" `echo ${lt[$j]}  | awk '{printf "%.1f", $1}'`
					get_lines $i ${lt[$j]} $j `echo ${lt[$j]}  | awk '{printf "%.2f", $1}'` 
					break
				fi
			done
		#fi
	done

sed -i '$ s/,$//g' $ProbabilitiesJsonFile
#  echo "]
# ,\"properties\":{\"advection_field\":\"http://thredds.socib.es/thredds/dodsC/operational_models/oceanographical/hydrodynamics/wmop/2015/04/roms_wmop_20150430.nc\",\"confidence_levels\":[$(echo ${lt[@]} | sed 's/ /,/g')],\"messages\":[{\"message\":\"Done!\",\"severity_level\":\"INFO\"}],\"num_confidence_levels\":1,\"num_time_instants\":1,\"time_instants\":[1430391600.0000000]},\"type\":\"FeatureCollection\"
# }"  >>$ProbabilitiesJsonFile
echo "]}" >>${ProbabilitiesJsonFile}

python3 ./CreateGeoJsons.py "${UniqId}" "/home/osf/SearchAndRescueTool" > creategeojsons_${UniqId}.log 2>&1


# ,\"properties\":{\"advection_field\":\"http://thredds.socib.es/thredds/dodsC/operational_models/oceanographical/hydrodynamics/wmop/2015/04/roms_wmop_20150430.nc\",\"confidence_levels\":[$(echo ${lt[@]} | sed 's/ /,/g')],\"messages\":[{\"message\":\"Done!\",\"severity_level\":\"INFO\"}],\"num_confidence_levels\":1,\"num_time_instants\":1,\"time_instants\":[1430391600.0000000]},\"type\":\"FeatureCollection\"
# }"  >>$ProbabilitiesJsonFile
exit
