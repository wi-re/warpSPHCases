<<hero>>

A membrane separates a dense, hot gas from a light, cold one. When it breaks, three waves leave the
interface: a rarefaction fan running into the dense gas, a contact discontinuity that marks the
original interface, and a shock running into the light gas. The solution is known exactly, which
makes the Sod tube the first thing a compressible solver is run against. This page runs it with
seven compressible schemes of warpSPH and compares each of them with the exact Riemann solution.

<<colab>>

## Origin and purpose

The problem is named after Sod, who used it in a survey of finite-difference schemes for
hyperbolic conservation laws {% cite sod1978 --file cases %}. It has since become the standard first
check for any compressible hydrodynamics method, including SPH {% cite monaghan2005 --file cases %}.

What it tests:

- **Shock capturing.** Does the scheme produce the right shock speed and jump, and how many smoothing
  lengths does it smear the shock over? Classic SPH needs artificial viscosity for this; Godunov-type
  and meshless schemes get dissipation from a Riemann solver instead.
- **Contact discontinuities.** A contact carries a jump in density and internal energy at constant
  pressure and velocity. Schemes that do not treat the two sides consistently show a pressure blip and
  an energy spike there.
- **Rarefaction.** A smooth expansion, where excess dissipation shows up as a rounded head and foot.
- **Conservation.** Total energy over the run.

## Setup

The warpSPH case lays the tube out in a periodic box so that no walls are needed: the box is
`[-1, 1]`, the physical tube is `0 < x < 1` with the diaphragm at `x = 0.5`, and the left half of the box is its
mirror image. The periodic wrap therefore acts as a reflecting boundary, and nothing reaches the box
ends before the end time. The dense gas occupies the middle half of the box and the light gas the outer
quarters, sampled so that every particle has the same mass (the light side is `samplingRatio = 4` times
coarser).

| quantity | value |
|---|---|
| left state (dense) | density 1, pressure 1, velocity 0 |
| right state (light) | density 0.25, pressure 0.1795, velocity 0 |
| equation of state | ideal gas, adiabatic index 5/3 |
| resolution `nx` | particles across the dense state's unit length, so `dx = 1/nx`; light side `nx/4` |
| kernel, neighbours | B7 spline, 8 neighbours (`n_h = 4`) in 1D |
| time stepping | Runge–Kutta 2, adaptive step with CFL factor 0.3, end time 0.15 |
| precision | float32 |

The states differ from the commonly quoted version (adiabatic index 1.4, right density 0.125 and
pressure 0.1); the exact solution below is computed for the states in the table, from the parameters stored
in each run.

Run the headline configuration with

<<command:CompSPH__default__nx400>>

The compared schemes are `CompSPH`, `Monaghan` (the classical 1992-style SPH step with artificial viscosity),
`CRKSPH` {% cite frontiere2017 --file cases %}, `GSPH` {% cite cha2003 --file cases %} and `InutsukaGSPH`
{% cite inutsuka2002 --file cases %} (Godunov SPH variants, no artificial viscosity), and the meshless
`MFM` and `MFV` {% cite hopkins2015 --file cases %}. `PESPH` is not assembled yet and is not shown.

## Results

<<figure:snapshots>>

<<figure:overlay>>

## Solver comparison

All seven schemes at the same resolution and end time, one row per scheme. The black line is the exact
solution; the number above each panel is the L1 error of that field (mean absolute deviation over the
particles of the tube).

<<figure:grid>>

<<table:comparison>>

<<figure:energy>>

## Reference comparison

Every error above is against the exact Riemann solution, sampled at the particle positions of the stored
frame and evaluated at that frame's own time. The convergence study repeats each scheme at five resolutions.

<<figure:convergence>>

<<table:orders>>

Because the solution contains a shock and a contact, the L1 error of a converging scheme is limited to
first order by the discontinuities, whatever the order of the scheme in smooth flow; the table gives the observed
order between consecutive resolutions and the figure compares the slopes with order 1 and 2 guide lines.

## Known limitations

- `PESPH` is registered but its scheme is not assembled yet, so it has no run here.
- Only the 1D tube is shown. The 2D and 3D extrusions (`sod2d`, `sod3d`) run in warpSPH and are not yet part of this page.
- All runs are float32 on a single GPU; the golden trajectories are compared with tolerances, not bit for bit.

## Reproduce

<<reproduce>>

## References

<<refs>>
