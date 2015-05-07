# test_gasturbine_network.py
# 
# Created:  Anil Variyar, March 2015
# Modified: 
#        

""" create and evaluate a gas turbine network
"""


# ----------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------

# suave imports
import SUAVE

# package imports
import numpy as np
import scipy as sp
import datetime
import time
from SUAVE.Core import Units

# python imports
import os, sys, shutil
from copy import deepcopy
from warnings import warn


from SUAVE.Core import Data, Data_Exception, Data_Warning
from SUAVE.Components import Component, Physical_Component, Lofted_Body
from SUAVE.Components import Component_Exception
from SUAVE.Components.Propulsors.Propulsor import Propulsor



def turbofan_sizing(turbofan,mach_number = None, altitude = None, delta_isa = 0, conditions = None):  
    
    
    #Unpack components
    
    #check if altitude is passed or conditions is passed
    
    if(conditions):
        #use conditions
        pass
        
    else:
        #check if mach number and temperature are passed
        if(mach_number==None or altitude==None):
            
            #raise an error
            raise NameError('The sizing conditions require an altitude and a Mach number')
        
        else:
            #call the atmospheric model to get the conditions at the specified altitude
            atmosphere = SUAVE.Analyses.Atmospheric.US_Standard_1976()
            p,T,rho,a,mu = atmosphere.compute_values(altitude)
        
            # setup conditions
            conditions = SUAVE.Analyses.Mission.Segments.Conditions.Aerodynamics()            
        
        
        
            # freestream conditions
            conditions_sizing.freestream.mach_number        = ones_1col*0.8 #*0.3
            conditions_sizing.freestream.pressure           = ones_1col*20000. #*100000.
            conditions_sizing.freestream.temperature        = ones_1col*215. #*258.0
            conditions_sizing.freestream.density            = ones_1col*0.8 #*1.225
        
            conditions_sizing.freestream.dynamic_viscosity          = ones_1col* 0.000001475 #*1.789*10**(-5)
            conditions_sizing.freestream.altitude           = ones_1col* 10. #* 0.5
        
            conditions_sizing.freestream.gravity            = ones_1col*9.81
            conditions_sizing.freestream.gamma              = ones_1col*1.4
            conditions_sizing.freestream.Cp                 = 1.4*287.87/(1.4-1)
            conditions_sizing.freestream.R                  = 287.87
            conditions_sizing.M = conditions_sizing.freestream.mach_number 
            conditions_sizing.T = conditions_sizing.freestream.temperature
            conditions_sizing.p = conditions_sizing.freestream.pressure
            conditions_sizing.freestream.speed_of_sound     = ones_1col* np.sqrt(conditions_sizing.freestream.Cp/(conditions_sizing.freestream.Cp-conditions_sizing.freestream.R)*conditions_sizing.freestream.R*conditions_sizing.freestream.temperature) #300.
            conditions_sizing.freestream.velocity           = conditions_sizing.M * conditions_sizing.freestream.speed_of_sound
            conditions_sizing.velocity = conditions_sizing.M * conditions_sizing.freestream.speed_of_sound
            conditions_sizing.q = 0.5*conditions_sizing.freestream.density*conditions_sizing.velocity**2
            conditions_sizing.g0 = conditions_sizing.freestream.gravity
            
            # propulsion conditions
            conditions_sizing.propulsion.throttle           =  ones_1col*1.0
    
    
    
    ram                       = turbofan.ram
    inlet_nozzle              = turbofan.inlet_nozzle
    low_pressure_compressor   = turbofan.low_pressure_compressor
    high_pressure_compressor  = turbofan.high_pressure_compressor
    fan                       = turbofan.fan
    combustor                 = turbofan.combustor
    high_pressure_turbine     = turbofan.high_pressure_turbine
    low_pressure_turbine      = turbofan.low_pressure_turbine
    core_nozzle               = turbofan.core_nozzle
    fan_nozzle                = turbofan.fan_nozzle
    thrust                    = turbofan.thrust
    
    
    
    #Creating the network by manually linking the different components
    
    
    #set the working fluid to determine the fluid properties
    ram.inputs.working_fluid                             = turbofan.working_fluid
    
    #Flow through the ram , this computes the necessary flow quantities and stores it into conditions
    ram(conditions)

    
    
    #link inlet nozzle to ram 
    inlet_nozzle.inputs.stagnation_temperature             = ram.outputs.stagnation_temperature #conditions.freestream.stagnation_temperature
    inlet_nozzle.inputs.stagnation_pressure                = ram.outputs.stagnation_pressure #conditions.freestream.stagnation_pressure
    
    #Flow through the inlet nozzle
    inlet_nozzle(conditions)
      
            
                    
    #--link low pressure compressor to the inlet nozzle
    low_pressure_compressor.inputs.stagnation_temperature  = inlet_nozzle.outputs.stagnation_temperature
    low_pressure_compressor.inputs.stagnation_pressure     = inlet_nozzle.outputs.stagnation_pressure
    
    #Flow through the low pressure compressor
    low_pressure_compressor(conditions)
    


    #link the high pressure compressor to the low pressure compressor
    high_pressure_compressor.inputs.stagnation_temperature = low_pressure_compressor.outputs.stagnation_temperature
    high_pressure_compressor.inputs.stagnation_pressure    = low_pressure_compressor.outputs.stagnation_pressure
    
    #Flow through the high pressure compressor
    high_pressure_compressor(conditions)
    
    
    
    #Link the fan to the inlet nozzle
    fan.inputs.stagnation_temperature                      = inlet_nozzle.outputs.stagnation_temperature
    fan.inputs.stagnation_pressure                         = inlet_nozzle.outputs.stagnation_pressure
    
    #flow through the fan
    fan(conditions)
    
    
    
    #link the combustor to the high pressure compressor
    combustor.inputs.stagnation_temperature                = high_pressure_compressor.outputs.stagnation_temperature
    combustor.inputs.stagnation_pressure                   = high_pressure_compressor.outputs.stagnation_pressure
    #combustor.inputs.nozzle_exit_stagnation_temperature = inlet_nozzle.outputs.stagnation_temperature
    
    #flow through the high pressor comprresor
    combustor(conditions)
    
    

    #link the high pressure turbione to the combustor
    high_pressure_turbine.inputs.stagnation_temperature    = combustor.outputs.stagnation_temperature
    high_pressure_turbine.inputs.stagnation_pressure       = combustor.outputs.stagnation_pressure
    high_pressure_turbine.inputs.fuel_to_air_ratio         = combustor.outputs.fuel_to_air_ratio
    #link the high pressuer turbine to the high pressure compressor
    high_pressure_turbine.inputs.compressor                = high_pressure_compressor.outputs
    #link the high pressure turbine to the fan
    high_pressure_turbine.inputs.fan                       = fan.outputs
    high_pressure_turbine.inputs.bypass_ratio              = 0.0 #set to zero to ensure that fan not linked here
    
    #flow through the high pressure turbine
    high_pressure_turbine(conditions)
            
    
    
    #link the low pressure turbine to the high pressure turbine
    low_pressure_turbine.inputs.stagnation_temperature     = high_pressure_turbine.outputs.stagnation_temperature
    low_pressure_turbine.inputs.stagnation_pressure        = high_pressure_turbine.outputs.stagnation_pressure
    #link the low pressure turbine to the low_pressure_compresor
    low_pressure_turbine.inputs.compressor                 = low_pressure_compressor.outputs
    #link the low pressure turbine to the combustor
    low_pressure_turbine.inputs.fuel_to_air_ratio          = combustor.outputs.fuel_to_air_ratio
    #link the low pressure turbine to the fan
    low_pressure_turbine.inputs.fan                        =  fan.outputs
    #get the bypass ratio from the thrust component
    low_pressure_turbine.inputs.bypass_ratio               =  thrust.bypass_ratio
    
    #flow through the low pressure turbine
    low_pressure_turbine(conditions)
    
    
    
    #link the core nozzle to the low pressure turbine
    core_nozzle.inputs.stagnation_temperature              = low_pressure_turbine.outputs.stagnation_temperature
    core_nozzle.inputs.stagnation_pressure                 = low_pressure_turbine.outputs.stagnation_pressure
    
    #flow through the core nozzle
    core_nozzle(conditions)
    
    

    #link the dan nozzle to the fan
    fan_nozzle.inputs.stagnation_temperature               = fan.outputs.stagnation_temperature
    fan_nozzle.inputs.stagnation_pressure                  = fan.outputs.stagnation_pressure
    
     # flow through the fan nozzle
    fan_nozzle(conditions)
    
    # compute the thrust using the thrust component
    
    
    
    #link the thrust component to the fan nozzle
    thrust.inputs.fan_exit_velocity                        = fan_nozzle.outputs.velocity
    thrust.inputs.fan_area_ratio                           = fan_nozzle.outputs.area_ratio
    thrust.inputs.fan_nozzle                               = fan_nozzle.outputs
    #link the thrust component to the core nozzle
    thrust.inputs.core_exit_velocity                       = core_nozzle.outputs.velocity
    thrust.inputs.core_area_ratio                          = core_nozzle.outputs.area_ratio
    thrust.inputs.core_nozzle                              = core_nozzle.outputs
    #link the thrust component to the combustor
    thrust.inputs.fuel_to_air_ratio                        = combustor.outputs.fuel_to_air_ratio
    #link the thrust component to the low pressure compressor 
    thrust.inputs.stag_temp_lpt_exit                       = low_pressure_compressor.outputs.stagnation_temperature
    thrust.inputs.stag_press_lpt_exit                      = low_pressure_compressor.outputs.stagnation_pressure

    #compute the trust
    thrust.size(conditions)
    
    
    
    
    
    #return
