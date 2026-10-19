# SPHERIC Test Case 10 -- data used on the sloshing-tank page

Source: SPHERIC benchmark test case 10 (sloshing wave impact), coordinated by A. Souto-Iglesias and E. Botia-Vera
(CEHINAV, Universidad Politecnica de Madrid); experiment described in Souto-Iglesias et al., Ocean Engineering 38
(2011), doi:10.1016/j.oceaneng.2011.09.008. The files in this folder are the test case's own material (description,
figures, repeatability registers) as distributed by SPHERIC, kept with attribution.

`lateral_water_1kHz.txt` is **derived** here from the test case's `lateral_water_1x.txt` (water, lateral impact, 18 %
filling, 1X tank; 20 kHz, 167001 samples, 8.35 s; the raw file is 10 MB and is not in git):

- every 20th row (1 kHz) for the roll columns (time, smoothed roll position in degrees, velocity, acceleration,
  original position), taken at the start of each 1 ms block. The roll motion is smooth, so this loses nothing the
  simulation uses (it linear-interpolates the smoothed position);
- column 2 `Pressure_1ms_mean[mbar]` is the mean of the 20 pressure samples of each 1 ms block (the raw column was
  replaced), column 7 `Pressure_1ms_max[mbar]` their maximum (added).

The 7-column layout keeps the original 6 so warpSPH's `sloshingTank` reads it unchanged (`rollDataFile`).
`Repeatability_Files/Water_4first_peak_lateral_impact_tto_0_85_H93_B1X.txt`: pressure (mbar) of the first four impacts
in each of the repeated experiments (the page uses the mean and the sample standard deviation).
Redistribution terms of the data are those of SPHERIC; confirm with the coordinators before publishing the repository.
