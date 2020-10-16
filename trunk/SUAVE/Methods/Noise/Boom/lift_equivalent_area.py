## @ingroupMethods-Noise-Boom
# lift_equivalent_area.py
# 
# Created:  Jul 2014, A. Wendorff
# Modified: Jan 2016, E. Botero

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------


import numpy as np
from SUAVE.Core import Data, Units

from SUAVE.Methods.Aerodynamics.Common.Fidelity_Zero.Lift import VLM


# ----------------------------------------------------------------------
#   Equivalent Area from lift for Sonic Boom
# ----------------------------------------------------------------------
## @ingroupMethods-Noise-Boom
def lift_equivalent_area(config,analyses,mach,aoa,altitude):
    
    conditions = Data()
    settings   = Data()
    settings.number_spanwise_vortices  = analyses.aerodynamics.settings.number_spanwise_vortices
    settings.number_chordwise_vortices = analyses.aerodynamics.settings.number_chordwise_vortices
    settings.model_fuselage            = True
    settings.propeller_wake_model      = None


    atmo_values = analyses.atmosphere.compute_values(altitude)
    p     = atmo_values.pressure
    a     = atmo_values.speed_of_sound
    gamma = atmo_values.ratio_of_specific_heats
    q     = 0.5*(mach**2)*gamma*p
    
    conditions.aerodynamics = Data()
    conditions.freestream   = Data()
    conditions.freestream.velocity          = np.array([mach*a]).T
    conditions.aerodynamics.angle_of_attack = np.array([aoa]).T
    conditions.freestream.mach_number       = np.array([mach]).T    
        
    CL, CDi, CM, CL_wing, CDi_wing, cl_y , cdi_y , CP ,Velocity_Profile = VLM(conditions, settings, config)
    
    print(CL)
    print(CDi)
    
    S   =  config.reference_area
    
    VD = analyses.aerodynamics.geometry.vortex_distribution
    
    areas      = VD.panel_areas
    normal_vec = VD.unit_normals
    XC         = VD.XC
    z_comp     = normal_vec[:,2]

    # Why do I need a 2 here????? But it works perfectly otherwise! Multiplied by 4 because the vlm multiplies by 4?
    lift_force_per_panel = 2*CP*q*z_comp*areas
    
    L_CP = np.sum(lift_force_per_panel)
    
    print(L_CP)
    
    # Check the lift forces
    L_CL = q*CL*S
    
    # Order the values
    sort_order = np.argsort(XC)
    X  = np.take(XC,sort_order)
    Y  = np.take(lift_force_per_panel, sort_order)

    u, inv = np.unique(X, return_inverse=True)
    sums   = np.zeros(len(u), dtype=Y.dtype) 
    np.add.at(sums, inv, Y) 
    
    lift_forces = sums
    X_locations = u
    
    summed_lift_forces = np.cumsum(lift_forces)
    
    beta = np.sqrt(conditions.freestream.mach_number[0][0]**2 -1)
    
    Ae_lift_at_each_x = (beta/(2*q[0]))*summed_lift_forces
    
    X_max  = config.total_length
    
    X_locs = np.concatenate([[0],X_locations,[X_max]])
    AE_x   = np.concatenate([[0],Ae_lift_at_each_x,[Ae_lift_at_each_x[-1]]])
    
    return X_locs, AE_x