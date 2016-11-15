#include <stdio.h>
#include <stdlib.h>
#include <python2.7/Python.h>

int main(int argc, char** argv) {
    setenv("PYTHONPATH",".",1);
    PyObject *pName, *pModule, *pDict, *pClass, *pInstance, *pValue, *pArgs;
    const char* fileName = "WcsRequest";
    const char* ClassName = "WcsRequest";
    const char* CoverageId =argv[1];

    // Initialize the Python Interpreter
    Py_Initialize();

    if (argc <7)
    {
        fprintf(stderr,"not enough arguments!\n"
                "ll_lon, ur_lon, ll_lat, ur_lat, t_s, (t_e)\n");
        return 1;
    }
    
    //variables
    const char* ll_lon = argv[2];
    const char* ur_lon = argv[3];
    const char* ll_lat = argv[4];
    const char* ur_lat = argv[5];
    const char* t_s = argv[6];
        
    //Python file
    pName = PyString_FromString(fileName);
    pModule = PyImport_Import(pName);

    pDict = PyModule_GetDict(pModule);
    
    // Build the name of a callable class 
    pClass = PyDict_GetItemString(pDict, ClassName);
    
    //Tuple with arguments
    pArgs = PyTuple_New(1);
    pValue =  PyString_FromString(CoverageId);
    PyTuple_SetItem(pArgs, 0, pValue);	
    
    // Create an instance of the class
    if (PyCallable_Check(pClass))
    {
        pInstance = PyObject_CallObject(pClass, pArgs); 
    }
    
    //Call functions
    //Call set_subset_x
    pValue = PyObject_CallMethod(pInstance, "set_subset_x", "(ss)", ll_lon, ur_lon);
    if (pValue)
    {
        Py_DECREF(pValue);
    }
    else
    {
        PyErr_Print();
    }
    
    //Call set_subset_y
    pValue = PyObject_CallMethod(pInstance, "set_subset_y", "(ss)", ll_lat, ur_lat);
    if (pValue)
    {
        Py_DECREF(pValue);
    }
    else
    {
        PyErr_Print();
    }
    
    if (argc ==8)
    {
        //Call set_subset_t with 2 arguments
        pValue = PyObject_CallMethod(pInstance, "set_subset_t", "(ss)", t_s, argv[7]);
        if (pValue)
        {
            Py_DECREF(pValue);
        }
        else
        {
            PyErr_Print();
        }
    }
    else
    {
        //Call set_subset_t with 1 argument
        pValue = PyObject_CallMethod(pInstance, "set_subset_t", "(s)", t_s);
        if (pValue)
        {
            Py_DECREF(pValue);
        }
        else
        {
            PyErr_Print();
        }
    }
    
    //Call get_results
    pValue = PyObject_CallMethod(pInstance, "get_result", "()");
    if (pValue)
    {
        Py_DECREF(pValue);
    }
    else
    {
        PyErr_Print();
    }
    
    // Clean up
    Py_DECREF(pModule);
    Py_DECREF(pName);
    Py_DECREF(pDict);
    Py_DECREF(pClass);
    Py_DECREF(pInstance);

    Py_DECREF(pArgs);

    // Finish the Python Interpreter
    Py_Finalize();

    return 0;
}

