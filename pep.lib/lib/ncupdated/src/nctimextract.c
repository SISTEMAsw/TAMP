#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netcdf.h>
#include <gdal.h>

#define TIME_DIMENTION	"Time"
#define REF_VARIABLE	"PM10"
// PM2.5 [µg/m³] =(so4ai+nh4ai+no3ai+naai+clai+orgaro1i+orgaro2i+orgalk1i+orgole1i+orgba1i+orgba2i+orgba3i+orgba4i+orgpai+eci+p25i+
//                 so4aj+nh4aj+no3aj+naaj+claj+orgaro1j+orgaro2j+orgalk1j+orgole1j+orgba1j+orgba2j+orgba3j+orgba4j+orgpaj+ecj+p25j)/ALT

// PM10[µg/m³] = PM2.5[µg/m³] + (antha+seas+soila)/alt



#define so4aj		0
#define nh4aj		1
#define no3aj		2
#define naaj		3
#define claj		4
#define orgaro1j	5
#define orgaro2j	6
#define orgalk1j	7
#define orgole1j	8
#define orgba1j		9
#define orgba2j		10
#define orgba3j		11
#define orgba4j		12
#define orgpaj		13
#define ecj		14
#define p25j		15

#define so4ai		16
#define nh4ai		17
#define no3ai		18
#define naai		19
#define clai		20
#define orgaro1i	21
#define orgaro2i	22
#define orgalk1i	23
#define orgole1i	24
#define orgba1i		25
#define orgba2i		26
#define orgba3i		27
#define orgba4i		28
#define orgpai		29
#define eci		30	
#define p25i		31


#define antha		32
#define seas		33
#define soila		34

#define PM2_5_DRY 	35	
#define PM10		36

#define DATASETS_NUMBER 37


struct dataset {
	char  	*name;
	float 	*data;
	int	size;
};

struct	dataset *Datasets = NULL; 

int initWorkSpace(int size){
	int i;
	printf("Init work space for computation after ...\n");
	Datasets = (struct dataset *)malloc(sizeof(struct dataset) * DATASETS_NUMBER);
	for ( i = 0; i < DATASETS_NUMBER; i++){
		Datasets[i].name = NULL; Datasets[i].data = NULL;
		Datasets[i].name = (char  *)malloc(sizeof(char  *) * 255 ); bzero(Datasets[i].name, 254);
		Datasets[i].data = (float *)malloc(sizeof(float) * size );
		if( Datasets[i].data == NULL ) { printf("malloc Datasets[%d].data\n", i); exit(1) ; }
		Datasets[i].size = size;
	}

	strcpy( Datasets[so4aj	  ].name, "so4aj"	);	strcpy( Datasets[so4ai	  ].name, "so4ai"	);
	strcpy( Datasets[nh4aj 	  ].name, "nh4aj"  	);	strcpy( Datasets[nh4ai 	  ].name, "nh4ai"  	);
	strcpy( Datasets[no3aj 	  ].name, "no3aj"  	);	strcpy( Datasets[no3ai 	  ].name, "no3ai"  	);
	strcpy( Datasets[naaj  	  ].name, "naaj"   	);	strcpy( Datasets[naai  	  ].name, "naai"   	);
	strcpy( Datasets[claj  	  ].name, "claj"   	);	strcpy( Datasets[clai  	  ].name, "clai"   	);
	strcpy( Datasets[orgaro1j ].name, "orgaro1j"	);	strcpy( Datasets[orgaro1i ].name, "orgaro1i"	);
	strcpy( Datasets[orgaro2j ].name, "orgaro2j"	);	strcpy( Datasets[orgaro2i ].name, "orgaro2i"	);
	strcpy( Datasets[orgalk1j ].name, "orgalk1j"	);	strcpy( Datasets[orgalk1i ].name, "orgalk1i"	);
	strcpy( Datasets[orgole1j ].name, "orgole1j"	);	strcpy( Datasets[orgole1i ].name, "orgole1i"	);
	strcpy( Datasets[orgba1j  ].name, "orgba1j"	);	strcpy( Datasets[orgba1i  ].name, "orgba1i"	);
	strcpy( Datasets[orgba2j  ].name, "orgba2j"	);	strcpy( Datasets[orgba2i  ].name, "orgba2i"	);
	strcpy( Datasets[orgba3j  ].name, "orgba3j"	);	strcpy( Datasets[orgba3i  ].name, "orgba3i"	);
	strcpy( Datasets[orgba4j  ].name, "orgba4j"	);	strcpy( Datasets[orgba4i  ].name, "orgba4i"	);
	strcpy( Datasets[orgpaj	  ].name, "orgpaj" 	);	strcpy( Datasets[orgpai	  ].name, "orgpai" 	);
	strcpy( Datasets[ecj	  ].name, "ecj"		);	strcpy( Datasets[eci	  ].name, "eci"		);
	strcpy( Datasets[p25j  	  ].name, "p25j"   	);	strcpy( Datasets[p25i  	  ].name, "p25i"   	);


	strcpy( Datasets[antha].name, "antha"  	);
	strcpy( Datasets[seas ].name, "seas "  	);
	strcpy( Datasets[soila].name, "soila"  	);


	strcpy( Datasets[PM2_5_DRY].name, "PM2_5_DRY"  	);
	strcpy( Datasets[PM10	  ].name, "PM10"  	);

	return 0;
}




int main(int argc, char **argv){
	int i, j, k, z, t;
	char	*nc_name_in	= NULL;
	char	*nc_name_out	= NULL;
	int	status		= -1;
	int	ncid_in		= -1;
	int	varid_in	= -1;
	int	ncid_out	= -1;
	int	*varid_out	= NULL;
	int	nd		= 0;
	int	*paDimIds 	= NULL;
	char	**dimname	= NULL;
	int	dimTot		= 0;
	int	dimOut		= 0;
	int	*dimids		= NULL;
	int	*dimReal	= NULL;
	int	nvars		= 0;
	int	*varids		= NULL;
	char	tmp[255];
	char	varname[255];
	unsigned char *data_in	= NULL;
	unsigned char *data_out	= NULL;
	float	*data		= NULL;
	float	*verticalData	= NULL;

	nc_type xtypep		= NC_FLOAT;
	int	nattsp		= 0;

	int	*timeSerie	= NULL;
	int	startIndex	= 0;
	int	numIndex	= 0;
	int	cubeSize	= 0;
	size_t 	t_len		= 0;
	char 	*coordinates	= NULL;
	char	*token		= NULL;
        size_t  xdim            = -1;
        size_t  ydim            = -1;
        size_t  ldim            = -1;
        size_t  tdim            = -1;
	float	*parser		= NULL;
	float	*parser_ori	= NULL;
	int	*parserInt	= NULL;
	int	*parserInt_ori	= NULL;

	float	*floor		= NULL;
	float	*floor_ori	= NULL;
	float	scaleFactor	= 5;
	int	offset		= 0;
	int	dIndex		= 0;



	char	**tiff_name	= NULL;


        GDALDatasetH    hSrcDS;
        GDALRasterBandH hBandSrc;
        int             pxSizeX                 = 0;
        int             pxSizeY                 = 0;
        int             types                   = 0;
        float           *data_tiff              = NULL;
        float           *data_ori              	= NULL;
        float           *data_coord[2]          = { NULL, NULL};
        double          padfGeoTransform[6]     = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
        double          invfGeoTransform[6]     = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
        double          x, y;


	nc_name_in  	= argv[1];
	nc_name_out 	= argv[2];
	scaleFactor	= atof(argv[3]);
	startIndex	= 4;

	for ( numIndex = 0, i = startIndex; argv[i] != NULL;  ) {
		i += 2; 
		if ( i > argc ) break; 
		numIndex++;
	}

	timeSerie = (int   *)malloc(sizeof(int)    * numIndex);
	tiff_name = (char **)malloc(sizeof(char *) * numIndex);


	for ( i = 0; i < numIndex; i++ ){
		j = (i*2) + startIndex;
		timeSerie[i] = atoi(argv[j]); 
		tiff_name[i] = (char *)malloc(sizeof(char) * 255); bzero(tiff_name[i], 254); strcpy(tiff_name[i], argv[j+1]); 
		printf("New layer time %d, PM10 %s ...\n", timeSerie[i], tiff_name[i]);
	}




	status = nc_open(nc_name_in, NC_NOWRITE, &ncid_in);
	if(status != NC_NOERR) { printf("nc_open in\n");	return 1; }

	status = nc_create(nc_name_out, NC_64BIT_OFFSET, &ncid_out);
	if(status != NC_NOERR) { printf("nc_create\n");       return 1; }



	//-----------------------------------//

	status = nc_inq_varids(ncid_in, &nvars, NULL);
	if(status != NC_NOERR) { printf("nc_inq_varids 1\n");      return 1; }

	varids		= (int *)malloc(sizeof(int) * nvars);
	varid_out	= (int *)malloc(sizeof(int) * nvars);

	status = nc_inq_varids(ncid_in, &nvars, varids);
	if(status != NC_NOERR) { printf("nc_inq_varids 2\n");      return 1; }

	printf("Found %d fields ...\n", nvars );

	nc_inq_varnatts(ncid_in, NC_GLOBAL, &nattsp);
	for ( k = 0; k < nattsp; k++){
		bzero(tmp, 254);
		nc_inq_attname(ncid_in, NC_GLOBAL, k, tmp);
		printf("Coyping global attribute %s ...\n", tmp );
		status = nc_copy_att (ncid_in, NC_GLOBAL, tmp, ncid_out, NC_GLOBAL);
		if ( status != NC_NOERR ) { printf("nc_copy_att %s\n", tmp);   return 1; }
	}


	for( i = 0; i < nvars; i++){
		bzero(varname, 254);
		status = nc_inq_varname(ncid_in, varids[i], varname);
		if (status != NC_NOERR) continue;

//		if ( strcmp(varname, REF_VARIABLE ) && strcmp(varname, "XLONG" ) && strcmp(varname, "XLAT" ) ) continue; // TO BE REMOVED


		// ------------------------------------------------------------------------- //
		printf("%d / %d - Processing %s ...\n", i+1, nvars, varname);

		status = nc_inq_varid(ncid_in, varname, &varid_in);
		if(status != NC_NOERR) { printf("nc_inq_varid in\n"); 	return 1; }

		status =  nc_inq_vartype(ncid_in, varid_in, &xtypep);
		if(status != NC_NOERR) { printf("nc_inq_vartype\n");   return 1; }


		nc_inq_varndims( ncid_in, varid_in, &nd );
		paDimIds = (int   *)malloc(nd * sizeof(int)   );
		dimname  = (char **)malloc(nd * sizeof(char *));
		dimids	 = (int   *)malloc(nd * sizeof(int)   );


		for (j = 0; j < nd; j++) { dimname[j]  = (char *)malloc(sizeof(char) * 255); bzero(dimname[j], 254); }

		nc_inq_vardimid( ncid_in, varid_in, paDimIds );

		dimTot = 1;
		for (j = 0; j < nd; j++) { 
			status = nc_inq_dimname (ncid_in, paDimIds[j], dimname[j]);
			if(status != NC_NOERR) { printf("nc_inq_dimname %d\n", j);   return 1; }
			size_t dim;
			nc_inq_dimlen( ncid_in, paDimIds[j], &dim );
			dimTot *= (int)dim;
			printf("Dimension name %s with dimention %d...\n", dimname[j], (int)dim);

		}


		// ------------------------------------------------------------------------- //

		printf("Reading layer ...\n");
		switch (xtypep) {
			case NC_FLOAT:
				data_in = (unsigned char *)malloc( dimTot * sizeof(float) );
				if(data_in == NULL)    { printf("malloc\n"); 		return 1; }
				status = nc_get_var_float(ncid_in, varid_in, (float *)data_in);
				if(status != NC_NOERR) { printf("nc_get_var_float\n"); 	return 1; }
				break;
			case NC_INT:
				data_in = (unsigned char *)malloc( dimTot * sizeof(int) );
				if(data_in == NULL)    { printf("malloc\n"); 		return 1; }
				status = nc_get_var_int(ncid_in, varid_in, (int *)data_in);
				if(status != NC_NOERR) { printf("nc_get_var_int\n"); 	return 1; }
				break;
			case NC_CHAR:
				data_in = (unsigned char *)malloc( dimTot * sizeof(char) );
				if(data_in == NULL)    { printf("malloc\n"); 		return 1; }
				status = nc_get_var_text(ncid_in, varid_in, (char *)data_in);
				if(status != NC_NOERR) { printf("nc_get_var_text\n"); 	return 1; }
				break;

			default:
				printf("%d type unkown\n", xtypep);
				return 1;
		}




		// ------------------------------------------------------------------------- //


		printf("Creating layer ...\n");
		dimOut     = 1;
		cubeSize   = 1;

		dimReal	 = (int   *)malloc(nd * sizeof(int)   );
		for (j = 0; j < nd; j++) {
			size_t dim;
			nc_inq_dimlen( ncid_in, paDimIds[j], &dim );
			if ( !strcmp(  dimname[j], TIME_DIMENTION ) ) 	dim = numIndex;
			else						cubeSize *= (int)dim;
			dimOut 	   *= (int)dim;
			dimReal[j]  = (int)dim;

			printf("Dimension output name %s with dimention %d...\n", dimname[j], (int)dim);
			status = nc_def_dim(ncid_out, dimname[j], dim, &(dimids[j])); 
			if ( status == NC_ENAMEINUSE ) status = nc_inq_dimid(ncid_out, dimname[j], &(dimids[j]));
			if ( status != NC_NOERR ) { printf("nc_def_dim %s dim %d %d\n", dimname[j], (int)dim, status);   return 1; } 
		}




		status = nc_def_var(ncid_out, varname, xtypep, nd, dimids, &(varid_out[i]));
		if (status != NC_NOERR) { printf("nc_def_var\n");        return 1; }

		nc_inq_varnatts(ncid_in, varid_in, &nattsp);
		for ( k = 0; k < nattsp; k++){
			bzero(tmp, 254);
			nc_inq_attname(ncid_in, varid_in, k, tmp);
			printf("Coyping attribute %s ...\n", tmp );
			status = nc_copy_att (ncid_in, varid_in, tmp, ncid_out, varid_out[i]);
			if ( status != NC_NOERR ) { printf("nc_copy_att %s\n", tmp);   return 1; }
		}


		// ------------------------------------------------------------------------- //

		printf("Extracting layer ...\n");
		status = nc_enddef(ncid_out);
		if (status != NC_NOERR) { printf("nc_enddef\n");        return 1; }

		switch (xtypep) {
			case NC_FLOAT:

				data_out = (unsigned char *)malloc( dimOut * sizeof(float) );
				if(data_out == NULL)    { printf("malloc\n"); 		return 1; }

				cubeSize = cubeSize * sizeof(float);
				xdim = dimReal[nd-1]; ydim = dimReal[nd-2]; ldim =  ( nd > 3 ) ? dimReal[nd-3] : 1;
				offset = ( xdim * ydim );
				dIndex = -1;
				if ( Datasets == NULL ) initWorkSpace( xdim *  ydim * numIndex );
				
				
				for ( j = 0 ; j < DATASETS_NUMBER; j++){
					if ( ! strcmp(varname, Datasets[j].name ) ) { dIndex = j; break; }
				}

				for( j = 0; j < numIndex; j++){
					memcpy(data_out + (j * cubeSize), data_in + (timeSerie[j] * cubeSize), cubeSize);

					if ( dIndex >= 0 ) {
						parser = (float *)(data_out + (j * cubeSize));
						memcpy( &(Datasets[dIndex].data[j * offset]) ,  parser, offset * sizeof(float) );

						for ( k = 0; k < ( xdim * ydim ) ; k++){
							for ( z = offset, t = 0 ; t < (ldim - 1) ; z += offset, t++ ) parser[k + z] = parser[k+z] / parser[k];
						}
					}	
					
				}


					


			        status = nc_put_var_float(ncid_out, varid_out[i], (float *)data_out);
				if(status != NC_NOERR) { printf("nc_put_var_float %d\n", status); return 1; }
				break;


			case NC_INT :
				data_out = (unsigned char *)malloc( dimOut * sizeof(int) );
				if(data_out == NULL)    { printf("malloc\n"); 		return 1; }

				cubeSize = cubeSize * sizeof(int);
				xdim = dimReal[nd-1]; ydim = dimReal[nd-2]; ldim =  ( nd > 3 ) ? dimReal[nd-3] : 1;
				offset = ( xdim * ydim );
				dIndex = -1;
				if ( Datasets == NULL ) initWorkSpace( xdim *  ydim * numIndex );
				
				
				for ( j = 0 ; j < DATASETS_NUMBER; j++){
					if ( ! strcmp(varname, Datasets[j].name ) ) { dIndex = j; break; }
				}

				for( j = 0; j < numIndex; j++){
					memcpy(data_out + (j * cubeSize), data_in + (timeSerie[j] * cubeSize), cubeSize);


						
					if ( dIndex >= 0 ) {
						parserInt = (int *)(data_out + (j * cubeSize));
						memcpy( &(Datasets[dIndex].data[j * offset]) ,  parserInt, offset * sizeof(int) );

						for ( k = 0; k < ( xdim * ydim ) ; k++){
							for ( z = offset, t = 0 ; t < (ldim - 1) ; z += offset, t++ ) parserInt[k + z] = parserInt[k+z] / parserInt[k];
						}
					}	
					
				}

			        status = nc_put_var_int(ncid_out, varid_out[i], (int *)data_out);
				if(status != NC_NOERR) { printf("nc_put_var_int %d\n", status); return 1; }
				break;

			case NC_CHAR:
				data_out = (unsigned char *)malloc( dimOut * sizeof(char) );
				if(data_out == NULL)    { printf("malloc\n");           return 1; }
				cubeSize = cubeSize * sizeof(char);


				for( j = 0; j < numIndex; j++){
					memcpy(data_out + (j * cubeSize), data_in + (timeSerie[j] * cubeSize), cubeSize);
				}


			        status = nc_put_var_text( ncid_out, varid_out[i], (char  *)data_out);
				if(status != NC_NOERR) { printf("nc_put_var_text\n"); 	return 1; }
				break;

			default:
				printf("%d type unkown\n", xtypep);
				return 1;
		}

		status = nc_redef(ncid_out);
		if (status != NC_NOERR) { printf("nc_redef\n");        return 1; }

		// ------------------------------------------------------------------------- //


		free(data_in);  data_in  = NULL;
		free(data_out); data_out = NULL;

		for (j = 0; j < nd; j++) free(dimname[j]);
		free(paDimIds);
	}

	status = nc_close(ncid_in);
	if (status != NC_NOERR) { printf("nc_close ncid_in\n"); return 1; }





	status = nc_enddef(ncid_out);
	if (status != NC_NOERR) { printf("nc_enddef\n");        return 1; }

	status = nc_sync(ncid_out);
	if(status != NC_NOERR) { printf("nc_sync %s\n", nc_strerror(status) ); return 1; }

// PM2.5 [µg/m³] =(so4ai+nh4ai+no3ai+naai+clai+orgaro1i+orgaro2i+orgalk1i+orgole1i+orgba1i+orgba2i+orgba3i+orgba4i+orgpai+eci+p25i+
//                 so4aj+nh4aj+no3aj+naaj+claj+orgaro1j+orgaro2j+orgalk1j+orgole1j+orgba1j+orgba2j+orgba3j+orgba4j+orgpaj+ecj+p25j)/ALT

// PM10[µg/m³] = PM2.5[µg/m³] + (antha+seas+soila)/alt

	for ( i = 0 ; i < Datasets[PM10].size ; i++){

		Datasets[antha   ].data[i] = Datasets[antha   ].data[i] / Datasets[PM10].data[i]; 
		Datasets[seas    ].data[i] = Datasets[seas    ].data[i] / Datasets[PM10].data[i];
		Datasets[soila   ].data[i] = Datasets[soila   ].data[i] / Datasets[PM10].data[i];

		Datasets[so4aj	 ].data[i] = Datasets[so4aj   ].data[i] / Datasets[PM10].data[i];
		Datasets[nh4aj	 ].data[i] = Datasets[nh4aj   ].data[i] / Datasets[PM10].data[i];
		Datasets[no3aj	 ].data[i] = Datasets[no3aj   ].data[i] / Datasets[PM10].data[i];
		Datasets[naaj	 ].data[i] = Datasets[naaj    ].data[i] / Datasets[PM10].data[i];
		Datasets[claj	 ].data[i] = Datasets[claj    ].data[i] / Datasets[PM10].data[i];
		Datasets[orgaro1j].data[i] = Datasets[orgaro1j].data[i] / Datasets[PM10].data[i];
		Datasets[orgaro2j].data[i] = Datasets[orgaro2j].data[i] / Datasets[PM10].data[i];
		Datasets[orgalk1j].data[i] = Datasets[orgalk1j].data[i] / Datasets[PM10].data[i];
		Datasets[orgole1j].data[i] = Datasets[orgole1j].data[i] / Datasets[PM10].data[i];
		Datasets[orgba1j ].data[i] = Datasets[orgba1j ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba2j ].data[i] = Datasets[orgba2j ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba3j ].data[i] = Datasets[orgba3j ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba4j ].data[i] = Datasets[orgba4j ].data[i] / Datasets[PM10].data[i];
		Datasets[orgpaj  ].data[i] = Datasets[orgpaj  ].data[i] / Datasets[PM10].data[i];
		Datasets[ecj	 ].data[i] = Datasets[ecj     ].data[i] / Datasets[PM10].data[i];
		Datasets[p25j	 ].data[i] = Datasets[p25j    ].data[i] / Datasets[PM10].data[i];

		Datasets[so4ai	 ].data[i] = Datasets[so4ai   ].data[i] / Datasets[PM10].data[i];
		Datasets[nh4ai	 ].data[i] = Datasets[nh4ai   ].data[i] / Datasets[PM10].data[i];
		Datasets[no3ai	 ].data[i] = Datasets[no3ai   ].data[i] / Datasets[PM10].data[i];
		Datasets[naai	 ].data[i] = Datasets[naai    ].data[i] / Datasets[PM10].data[i];
		Datasets[clai	 ].data[i] = Datasets[clai    ].data[i] / Datasets[PM10].data[i];
		Datasets[orgaro1i].data[i] = Datasets[orgaro1i].data[i] / Datasets[PM10].data[i];
		Datasets[orgaro2i].data[i] = Datasets[orgaro2i].data[i] / Datasets[PM10].data[i];
		Datasets[orgalk1i].data[i] = Datasets[orgalk1i].data[i] / Datasets[PM10].data[i];
		Datasets[orgole1i].data[i] = Datasets[orgole1i].data[i] / Datasets[PM10].data[i];
		Datasets[orgba1i ].data[i] = Datasets[orgba1i ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba2i ].data[i] = Datasets[orgba2i ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba3i ].data[i] = Datasets[orgba3i ].data[i] / Datasets[PM10].data[i];
		Datasets[orgba4i ].data[i] = Datasets[orgba4i ].data[i] / Datasets[PM10].data[i];
		Datasets[orgpai  ].data[i] = Datasets[orgpai  ].data[i] / Datasets[PM10].data[i];
		Datasets[eci	 ].data[i] = Datasets[eci     ].data[i] / Datasets[PM10].data[i];
		Datasets[p25i	 ].data[i] = Datasets[p25i    ].data[i] / Datasets[PM10].data[i];

		Datasets[PM2_5_DRY].data[i] = Datasets[PM2_5_DRY].data[i] / Datasets[PM10].data[i];

		Datasets[PM10].data[i] 		= 1.0;

	}


        // ---------------------------------------------------- // 
        GDALAllRegister();
        // ---------------------------------------------------- // 

	
	printf("Loading layer %s ...\n", REF_VARIABLE );

	status = nc_inq_varid(ncid_out, REF_VARIABLE, &varid_in);
	if(status != NC_NOERR) { printf("nc_inq_varid\n"); 	return 1; }

	nc_inq_varndims( ncid_out, varid_in, &nd );
	paDimIds = (int   *)malloc(nd * sizeof(int)   );
	dimids	 = (int   *)malloc(nd * sizeof(int)   );



	nc_inq_vardimid( ncid_out, varid_in, paDimIds );

	for (j = 0; j < nd; j++) { 
		size_t dim;
		nc_inq_dimlen( ncid_out, paDimIds[j], &dim );
		dimTot *= (int)dim;
	}

        nc_inq_dimlen ( ncid_out, paDimIds[nd-1], &xdim );
        nc_inq_dimlen ( ncid_out, paDimIds[nd-2], &ydim );
        nc_inq_dimlen ( ncid_out, paDimIds[nd-3], &ldim );
        nc_inq_dimlen ( ncid_out, paDimIds[nd-4], &tdim );

	dimTot = (int)xdim * (int)ydim * (int)ldim * (int)tdim;

	data = (float *)malloc( dimTot * sizeof(float) );
	if(data == NULL) { printf("malloc\n");	return 1; }

	data_ori = (float *)malloc( dimTot * sizeof(float) );
	if(data_ori == NULL) { printf("malloc\n");	return 1; }



	verticalData = (float *)malloc( ldim * sizeof(float) );
	if(verticalData == NULL) { printf("malloc\n");	return 1; }

	status = nc_get_var_float(ncid_out, varid_in, data);
	if(status != NC_NOERR) { printf("nc_get_var_float %s\n", nc_strerror(status) ); return 1; }

	status = nc_inq_attlen( ncid_out, varid_in, "coordinates", &t_len);
	if (status != NC_NOERR) { printf("nc_inq_attlen %s\n", nc_strerror(status) ); return 1; }
	coordinates = (char *) malloc(t_len + 1); 

	status = nc_get_att_text(ncid_out, varid_in, "coordinates", coordinates);
	if (status != NC_NOERR) { printf("nc_get_att_text %s\n", nc_strerror(status) ); return 1; }
	coordinates[t_len] = '\0';

	printf("Coordinates for this layer %s ...\n", coordinates);

        // ---------------------------------------------------- // 

	for ( token = strtok(coordinates, " "), i = 0; token != NULL ;  token = strtok(NULL, " "), i++ ){
		if ( i > 1 ) break;
		printf("Loading %s ...\n", token);

	        data_coord[i] = (float *)malloc( (int)xdim * (int)ydim * (int)tdim * sizeof(float) );
	        if(data_coord[i] == NULL)    { printf("malloc\n");      return 1; }

		status = nc_inq_varid(ncid_out, token, &varid_in);
		if(status != NC_NOERR) { printf("nc_inq_varid\n"); 	return 1; }

		status = nc_get_var_float(ncid_out, varid_in, data_coord[i]);
		if(status != NC_NOERR) { printf("nc_get_var_float %s\n", nc_strerror(status) ); return 1; }
	}

        // ---------------------------------------------------- // 
	// TO BE REMOVE !!!

        if ( (hSrcDS = GDALOpen( "coord.tif", GA_ReadOnly )) != NULL ) {
        	printf("Using external coordinates file ... \n");
	        pxSizeX  = GDALGetRasterXSize(hSrcDS);
	        pxSizeY  = GDALGetRasterYSize(hSrcDS);


		if ( pxSizeX != (int)xdim ) {
			printf("coord.tif wrong dimention x: %d != %d\n", pxSizeX, (int)xdim );			
			return 1;
		}

		if ( pxSizeY != (int)ydim ) {
			printf("coord.tif wrong dimention y: %d != %d\n", pxSizeY, (int)ydim );			
			return 1;
		}

		float *temp_coord = NULL;
		temp_coord = (float *)malloc( sizeof(float) * pxSizeX * pxSizeY );
	        if(temp_coord == NULL) { printf("malloc\n");      return 1; }

		hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
		types    = GDALGetRasterDataType(hBandSrc);
		GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, temp_coord, pxSizeX, pxSizeY, types, 0, 0);


		for ( i = 0 ; i < ( (int)xdim * (int)ydim ); i++) {
			x = ( i % (int)xdim );
			y = ( i / (int)xdim );
			y = (int)ydim - y - 1;
			j = x + ( y * (int)xdim );
			data_coord[1][i] = temp_coord[j];
		}


		hBandSrc = GDALGetRasterBand( hSrcDS, 2 );
		types    = GDALGetRasterDataType(hBandSrc);
		GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, temp_coord, pxSizeX, pxSizeY, types, 0, 0);
		GDALClose(hSrcDS);

		for ( i = 0 ; i < ( (int)xdim * (int)ydim ); i++) {
			x = ( i % (int)xdim );
			y = ( i / (int)xdim );
			y = (int)ydim - y - 1;
			j = x + ( y * (int)xdim );
			data_coord[0][i] = temp_coord[j];
		}


		for ( j = 0; j < numIndex; j++ ){
			for ( i = 0 ; i < ( (int)xdim * (int)ydim ); i++) {
				data_coord[0][i + ( (int)xdim * (int)ydim * j )] = data_coord[0][i];
				data_coord[1][i + ( (int)xdim * (int)ydim * j )] = data_coord[1][i];

			}
		}		
	}
        // ---------------------------------------------------- // 

	for ( j = 0; j < numIndex; j++ ){

	        printf("Loading new layer %s for time %d ...\n", REF_VARIABLE, timeSerie[j]);

	        if ( (hSrcDS = GDALOpen( tiff_name[j], GA_ReadOnly )) == NULL ){
	                printf("Unable open src file %s\n", tiff_name[j]);
	                return 1;
	        }

	        pxSizeX  = GDALGetRasterXSize(hSrcDS);
	        pxSizeY  = GDALGetRasterYSize(hSrcDS);
	        hBandSrc = GDALGetRasterBand( hSrcDS, 1 );
	        types    = GDALGetRasterDataType(hBandSrc);
	        data_tiff = (float *)malloc( GDALGetDataTypeSize(types)/8 *  pxSizeX * pxSizeY);
	        if(data_tiff == NULL)    { printf("malloc\n");  return 1; }

	        data_ori  = (float *)malloc( sizeof(float) *  (int)xdim * (int)ydim );
	        if(data_ori == NULL)    { printf("malloc\n");  return 1; }



	        if ( GDALGetGeoTransform( hSrcDS, padfGeoTransform ) == CE_Failure ){
	                printf("Image no transform can be fetched...\n");
	                return 1;
	        }
	        if ( GDALInvGeoTransform(padfGeoTransform,invfGeoTransform) == FALSE ){
	                printf("Problem with inversion of matrix\n");
	                return 3;
	        }

	        GDALRasterIO( hBandSrc, GF_Read, 0, 0, pxSizeX, pxSizeY, data_tiff, pxSizeX, pxSizeY, types, 0, 0);
	        GDALClose(hSrcDS);

	        // ---------------------------------------------------- // 


		printf("Updating layer %d ...\n" , j);
		
		offset = ( (int)xdim * (int)ydim );
		for ( i = 0 ; i < ( (int)xdim * (int)ydim ); i++) {			

			z = ( j * (int)xdim * (int)ydim ) + i;	
			data_ori[z] = data[z];
        	        GDALApplyGeoTransform( invfGeoTransform, data_coord[0][z], data_coord[1][z], &x, &y);

        	        if ( (int)x < 0 )          continue;
 	      	        if ( (int)y < 0 )          continue;
        	        if ( (int)x >= pxSizeX )   continue;
        	        if ( (int)y >= pxSizeY )   continue;
        	        k = (int)x + ( (int)y * pxSizeX);

        	        if ( data_tiff[k] <= 0.0 ) continue; 
			fprintf(stderr, "%d\t%d\t%f\t%f\n", (int)x, (int)y , data[z], data_tiff[k]);
        		data[z] 	= data_tiff[k];
		}
		
		free(data_tiff);
	}



	status = nc_inq_varids(ncid_out, &nvars, NULL);
	if(status != NC_NOERR) { printf("nc_inq_varids 1\n");      return 1; }
	varids	= (int *)malloc(sizeof(int) * nvars);


	status = nc_inq_varids(ncid_out, &nvars, varids);
	if(status != NC_NOERR) { printf("nc_inq_varids ncid_out\n");      return 1; }

	for( i = 0; i < nvars; i++){

		bzero(varname, 254);
		status = nc_inq_varname(ncid_out, varids[i], varname);
		if (status != NC_NOERR) continue;

		dIndex = -1;
		for ( j = 0 ; j < DATASETS_NUMBER; j++){
			if ( ! strcmp(varname, Datasets[j].name ) ) { dIndex = j; break; }
		}

		if ( dIndex < 0 ) continue;		

		printf("Updating ground layer for %s ...\n", varname );

		status = nc_inq_varid(ncid_out, varname, &varid_in);
		if(status != NC_NOERR) { printf("nc_inq_varid in\n"); 	return 1; }

		nc_inq_vardimid( ncid_out, varid_in, paDimIds );

	        nc_inq_dimlen ( ncid_out, paDimIds[nd-1], &xdim );
	        nc_inq_dimlen ( ncid_out, paDimIds[nd-2], &ydim );
	        nc_inq_dimlen ( ncid_out, paDimIds[nd-3], &ldim );
	        nc_inq_dimlen ( ncid_out, paDimIds[nd-4], &tdim );

		dimTot = (int)xdim * (int)ydim * (int)ldim * (int)tdim;
		offset = (int)xdim * (int)ydim;

		parser = (float *)malloc( dimTot * sizeof(float) );
		if(parser == NULL)    { printf("malloc\n");            return 1; }

		parser_ori = (float *)malloc( dimTot * sizeof(float) );
		if(parser_ori == NULL) { printf("malloc\n");            return 1; }

		parserInt = (int *)malloc( dimTot * sizeof(int) );
		if(parserInt == NULL)    { printf("malloc\n");            return 1; }

		parserInt_ori = (int*)malloc( dimTot * sizeof(int) );
		if(parserInt_ori == NULL) { printf("malloc\n");            return 1; }




		status = nc_get_var_float(ncid_out, varid_in, parser);
		if(status != NC_NOERR) { printf("nc_get_var_float\n"); 	return 1; }

		float ref = 0.0;


		
		for ( j = 0; j < numIndex; j++ ){
			for ( k = ( offset * j ), z = ( (int)xdim * (int)ydim * (int)ldim * j );  k < ( offset * (j+1) ); k++, z++ ){
				parser[z] 	= Datasets[dIndex].data[k] * data[k];
				parser_ori[z] 	= Datasets[dIndex].data[k] * data_ori[k];
			}

			floor 	  = &(parser[     ( (int)xdim * (int)ydim * (int)ldim * j ) ]);
			floor_ori = &(parser_ori[ ( (int)xdim * (int)ydim * (int)ldim * j ) ]);

			for ( k = 0; k < ( xdim * ydim ) ; k++){
				if (  ( floor_ori[k] * scaleFactor ) > floor[k] ) 	ref = floor[k];
				else							ref = floor_ori[k];
				
				for ( z = offset, t = 0 ; t < (ldim - 1) ; z += offset, t++ ) floor[k+z] = floor[k+z] * ref;
				
			}
	
			

		}

		status = nc_put_var_float(ncid_out, varid_in, parser);
		if(status != NC_NOERR) { printf("nc_put_var_float\n"); 	return 1; }

		free(parser); parser = NULL;
	}


        // ---------------------------------------------------- // 


	status = nc_close(ncid_out);
	if (status != NC_NOERR) { printf("nc_close ncid_out %s\n",  nc_strerror(status) ); return 1; }

	printf("Done.\n");	

	return 0;
}
