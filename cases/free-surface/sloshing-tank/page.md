<<hero>>

A rectangular tank half-filled with a shallow layer of water is rolled back and forth about the centre of its floor,
close to the first sloshing period. Once per cycle the water runs up the tank as a travelling wave and hits the end
wall, and a pressure sensor in the wall records a short, sharp impact. Predicting that pressure history is the
benchmark: SPHERIC test case 10. This page reproduces its lateral water impact with warpSPH, with the weakly
compressible δ-SPH scheme and with an incompressible scheme, and compares the sensor pressure with the experiment.

<<colab>>

## Origin and purpose

Test case 10 of the SPHERIC benchmark series was set up by the model basin group of the Universidad Politécnica de
Madrid; the experiment, the sensors and the data processing are described by Souto-Iglesias et al.
{% cite soutoiglesias2011 --file cases %}. The test case provides the recorded pressure histories of the first four
impacts, the corresponding roll angle history of the tank, and a repeatability register: the peak pressure of the
first four impacts in about a hundred repeated experiments.

What it tests:

- **Free-surface flow with violent impacts.** The wave overturns and breaks against the wall; a scheme has to carry
  the free surface, the run-up and the impact without losing particles or inventing pressure.
- **Wall pressure.** The benchmark quantity is the pressure at a wall sensor, so the wall treatment matters as much
  as the fluid scheme. The page runs the case with boundary particles and with analytic walls.
- **Timing.** The arrival time of each impact depends on the whole sloshing dynamics, not only on the impact itself.

## Setup

The tank is 0.900 m wide and 0.508 m high and holds water to a depth of 0.093 m (18 % filling); the experimental tank
is 62 mm thick, the simulation is two-dimensional. The tank rolls about the centre of its floor following the recorded
roll angle (amplitude about 4°, period 0.85 times the first sloshing period of 1.919 s). The simulation runs in the
frame that rolls with the tank and rotates the direction of gravity with the recorded angle; this leaves out the
inertial (Euler and centrifugal) forces of the non-inertial frame. Sensor 1 sits on the left wall at the still-water
line, at `(-0.45, 0.093)` m in the tank frame.

| quantity | value |
|---|---|
| fluid | water, rest density 1000 kg/m³, single phase (the air is not modelled) |
| weakly compressible scheme | `deltaSPH` {% cite marrone2011 --file cases %}, inviscid with artificial viscosity α = 0.02, numerical sound speed 20 m/s, Wendland C4, symplectic Euler with a fixed step of 10⁻⁴ s, 4 neighbours per support radius (`n_h` 4) |
| incompressible scheme | `omniIncompressible` (a port of the omniSPH incompressible loop), Wendland C2, semi-implicit Euler, CFL factor 0.2, step of at most 10⁻³ s, `n_h` 2.57 (and 4 for one analytic-wall run, to show the dependence on the support) |
| walls | boundary particles with modified dynamic boundary conditions {% cite english2022 --file cases %}, or analytic walls |
| resolution | `nx` = tank width / particle spacing; 200 gives a spacing of 4.5 mm |
| roll motion | the recorded roll history of the experiment, 7.5 s |
| sensor pressure | pressure of the fluid particles within 2 cm of the sensor, Gaussian-weighted (Shepard); with fewer than three particles in range there is no reading, counted as zero in the impulse |
| precision | float32 |

Run the headline configuration with

<<command:deltaSPH__default__nx200>>

(pass `--rollDataFile` with the roll history from this page's `reference/spheric-tc10` folder).

## Results

<<figure:trace>>

<<figure:snapshots>>

## Solver comparison

<<table:comparison>>

**Like with like.** A sharp raw pressure peak and a smoothed one are not comparable, and the raw reading of a particle
simulation is a noisy few-millisecond event. Simulations and the recorded trace are therefore smoothed the same way (a
Gaussian of 10 ms width that skips the instants at which the sensor has no fluid around it) before their peaks are
compared. `peak k` is the maximum of the smoothed pressure within 0.15 s of the k-th experimental impact; the first row
is the recorded trace smoothed the same way. `impulse / exp` is the (unsmoothed) pressure impulse within 0.1 s of each
impact relative to the recorded trace, averaged over the four impacts; `mean |dt|` is the mean timing difference of the
smoothed simulated and recorded peaks.

## Reference comparison

The reference is the experiment: the recorded sensor trace (reduced to 1 kHz, see `PROVENANCE.md` in the page folder).
It is a single experiment: the repeatability register in the same folder (the raw peak of each impact in about a hundred
repetitions) shows that impact peaks scatter strongly from one repetition to the next, so a single recorded trace is a
yardstick of a given width, not a point.

<<figure:sweep>>

<<table:resolution>>

## Known limitations

- **Smoothed peaks, not raw ones.** The comparison is made on pressure smoothed with a 10 ms Gaussian, for the simulations
  and the recording alike; the peak values depend on that width. The raw few-millisecond peak of a particle simulation is
  not comparable with the raw peak of a sensor of finite size and bandwidth.
- **The peak pressure depends on the support** (`n_h`): the table labels say which support a run uses, and runs at
  different `n_h` are not like for like. The simulations are single phase, the experiment has an air cushion.
- The simulation is two-dimensional; the experimental tank has side walls 62 mm apart, and the roll motion enters
  through the rotated gravity vector without the inertial forces of the rolling frame.
- The Gaussian-weighted probe around the sensor, not the pressure of a single wall particle, is what is compared.
- The recorded trace covers one experiment; the simulation is compared with it impact by impact, not by a statistic
  over repetitions, except for the peak heights.
- All runs are float32 on a single GPU; the golden trajectory is compared with a tolerance, not bit for bit.

## Reproduce

<<reproduce>>

## References

<<refs>>
